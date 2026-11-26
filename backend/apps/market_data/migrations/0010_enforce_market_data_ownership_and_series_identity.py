import django.db.models.deletion
import uuid
from django.db import migrations, models


def assign_unambiguous_series(apps, schema_editor):
    """Attach legacy published observations only when exactly one exact series matches."""
    alias = schema_editor.connection.alias
    Observation = apps.get_model('market_data', 'PriceObservation')
    Series = apps.get_model('market_data', 'MarketDataSeries')
    rows = Observation.objects.using(alias).filter(status='PUBLISHED', series_id__isnull=True).iterator(chunk_size=500)
    for observation in rows:
        matches = Series.objects.using(alias).filter(
            instrument_id=observation.instrument_id,
            price_type=observation.price_type,
            currency=observation.currency,
            unit=observation.unit,
            source=observation.source,
            is_active=True,
        ).values_list('id', flat=True)[:2]
        matches = list(matches)
        if len(matches) == 1:
            Observation.objects.using(alias).filter(pk=observation.pk).update(series_id=matches[0])


def deduplicate_instrument_sync_events(apps, schema_editor):
    from django.db.models import Count
    alias = schema_editor.connection.alias
    Event = apps.get_model('market_data', 'InstrumentSyncEvent')
    duplicate_keys = list(Event.objects.using(alias).values(
        'instrument_id', 'identity_version'
    ).annotate(total=Count('id')).filter(total__gt=1).values_list(
        'instrument_id', 'identity_version'
    ))
    for instrument_id, identity_version in duplicate_keys:
        event_ids = list(Event.objects.using(alias).filter(
            instrument_id=instrument_id, identity_version=identity_version
        ).order_by('-created_at', '-id').values_list('id', flat=True))
        if len(event_ids) > 1:
            Event.objects.using(alias).filter(id__in=event_ids[1:]).delete()


def deduplicate_publication_events(apps, schema_editor):
    from django.db.models import Count
    alias = schema_editor.connection.alias
    Event = apps.get_model('market_data', 'MarketDataPublicationEvent')
    duplicate_ids = list(Event.objects.using(alias).values('observation_id').annotate(
        total=Count('id')
    ).filter(total__gt=1).values_list('observation_id', flat=True))
    for observation_id in duplicate_ids:
        event_ids = list(Event.objects.using(alias).filter(
            observation_id=observation_id
        ).order_by('created_at', 'id').values_list('id', flat=True))
        if len(event_ids) > 1:
            Event.objects.using(alias).filter(id__in=event_ids[1:]).delete()


def install_published_observation_guard(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    schema_editor.execute("""
        CREATE OR REPLACE FUNCTION pm_guard_published_observation_immutable()
        RETURNS trigger AS $$
        BEGIN
            IF OLD.status = 'PUBLISHED' THEN
                RAISE EXCEPTION 'Published price observations are immutable; create a correction.';
            END IF;
            IF TG_OP = 'DELETE' THEN
                RETURN OLD;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    schema_editor.execute('DROP TRIGGER IF EXISTS trg_pm_published_observation_immutable ON price_observations;')
    schema_editor.execute("""
        CREATE TRIGGER trg_pm_published_observation_immutable
        BEFORE UPDATE OR DELETE ON price_observations
        FOR EACH ROW EXECUTE FUNCTION pm_guard_published_observation_immutable();
    """)
    schema_editor.execute("""
        CREATE OR REPLACE FUNCTION pm_guard_market_series_identity()
        RETURNS trigger AS $$
        BEGIN
            IF ROW(NEW.instrument_id, NEW.exchange, NEW.source, NEW.price_type, NEW.currency,
                   NEW.unit, NEW.pricing_methodology, NEW.adjustment_methodology, NEW.market_timezone)
               IS DISTINCT FROM
               ROW(OLD.instrument_id, OLD.exchange, OLD.source, OLD.price_type, OLD.currency,
                   OLD.unit, OLD.pricing_methodology, OLD.adjustment_methodology, OLD.market_timezone)
               AND EXISTS (SELECT 1 FROM price_observations WHERE series_id = OLD.id) THEN
                RAISE EXCEPTION 'Market data series identity is immutable after observations exist.';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    schema_editor.execute('DROP TRIGGER IF EXISTS trg_pm_market_series_identity ON market_data_series;')
    schema_editor.execute("""
        CREATE TRIGGER trg_pm_market_series_identity
        BEFORE UPDATE ON market_data_series
        FOR EACH ROW EXECUTE FUNCTION pm_guard_market_series_identity();
    """)


def remove_published_observation_guard(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    schema_editor.execute('DROP TRIGGER IF EXISTS trg_pm_published_observation_immutable ON price_observations;')
    schema_editor.execute('DROP FUNCTION IF EXISTS pm_guard_published_observation_immutable();')
    schema_editor.execute('DROP TRIGGER IF EXISTS trg_pm_market_series_identity ON market_data_series;')
    schema_editor.execute('DROP FUNCTION IF EXISTS pm_guard_market_series_identity();')


class Migration(migrations.Migration):
    dependencies = [('market_data', '0009_remove_priceobservation_uniq_published_obs_and_more')]

    operations = [
        # Both old fields already use UUID database columns with db_constraint=False.
        # Change Django state to scalar UUIDs without dropping/recreating stored values.
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.RemoveIndex(model_name='marketdatapoint', name='mdp_inst_time_idx'),
                migrations.RemoveIndex(model_name='marketdatapoint', name='mdp_inst_int_time_idx'),
                migrations.RemoveIndex(model_name='providerinstrumentmapping', name='pim_prov_inst_idx'),
                migrations.AlterUniqueTogether(name='marketdatapoint', unique_together=set()),
                migrations.RemoveField(model_name='marketdatapoint', name='instrument'),
                migrations.AddField(
                    model_name='marketdatapoint', name='instrument_id',
                    field=models.UUIDField(db_column='instrument_id', db_index=True),
                ),
                migrations.RemoveField(model_name='providerinstrumentmapping', name='instrument'),
                migrations.AddField(
                    model_name='providerinstrumentmapping', name='instrument_id',
                    field=models.UUIDField(db_column='instrument_id', db_index=True, help_text='Canonical Instrument UUID in primary database'),
                ),
                migrations.AddIndex(
                    model_name='marketdatapoint',
                    index=models.Index(fields=['instrument_id', '-timestamp'], name='mdp_inst_time_idx'),
                ),
                migrations.AddIndex(
                    model_name='marketdatapoint',
                    index=models.Index(fields=['instrument_id', 'interval', '-timestamp'], name='mdp_inst_int_time_idx'),
                ),
                migrations.AddIndex(
                    model_name='providerinstrumentmapping',
                    index=models.Index(fields=['provider_name', 'instrument_id'], name='pim_prov_inst_idx'),
                ),
                migrations.AlterUniqueTogether(
                    name='marketdatapoint', unique_together={('instrument_id', 'timestamp', 'interval', 'provider')}
                ),
            ],
        ),
        migrations.RunPython(
            deduplicate_instrument_sync_events, migrations.RunPython.noop,
            hints={'model_name': 'instrumentsyncevent'},
        ),
        migrations.AddConstraint(
            model_name='instrumentsyncevent',
            constraint=models.UniqueConstraint(fields=('instrument_id', 'identity_version'), name='uniq_instrument_sync_version'),
        ),
        migrations.RunPython(
            deduplicate_publication_events, migrations.RunPython.noop,
            hints={'model_name': 'marketdatapublicationevent'},
        ),
        migrations.AddConstraint(
            model_name='marketdatapublicationevent',
            constraint=models.UniqueConstraint(fields=('observation_id',), name='uniq_pub_event_observation'),
        ),
        migrations.RemoveConstraint(model_name='priceobservation', name='uniq_published_obs'),
        migrations.AddConstraint(
            model_name='priceobservation',
            constraint=models.UniqueConstraint(
                condition=models.Q(('status', 'PUBLISHED'), ('correction_of__isnull', True)),
                fields=('instrument_id', 'series', 'effective_at', 'price_type', 'source'),
                name='uniq_published_obs_series',
            ),
        ),
        migrations.AlterField(
            model_name='priceobservation', name='instrument_id',
            field=models.UUIDField(db_index=True, help_text='Canonical Instrument UUID (Primary DB)'),
        ),
        migrations.AlterField(
            model_name='instrumentcoverage', name='instrument_id',
            field=models.UUIDField(db_index=True, help_text='Canonical Instrument UUID (Primary DB)', unique=True),
        ),
        migrations.AlterField(
            model_name='marketdataworklistitem', name='instrument_id',
            field=models.UUIDField(db_index=True, help_text='Canonical Instrument UUID (Primary DB)'),
        ),
        migrations.AlterField(
            model_name='priceimportbatch', name='user_id',
            field=models.UUIDField(db_index=True, help_text='Uploader User UUID (Primary DB)'),
        ),
        migrations.AlterField(
            model_name='marketinstrumentreference', name='id',
            field=models.UUIDField(editable=False, help_text='Canonical Instrument UUID', primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='priceobservation', name='series',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                related_name='observations', to='market_data.marketdataseries',
            ),
        ),
        migrations.RunPython(
            assign_unambiguous_series, migrations.RunPython.noop,
            hints={'model_name': 'priceobservation'},
        ),
        migrations.RunPython(
            install_published_observation_guard, remove_published_observation_guard,
            hints={'model_name': 'priceobservation'},
        ),
        migrations.AlterField(
            model_name='priceobservation', name='trust_class',
            field=models.CharField(
                choices=[
                    ('VERIFIED_OFFICIAL', 'Verified Official'),
                    ('VERIFIED_PERMITTED_SECONDARY', 'Verified Permitted Secondary'),
                    ('MANUAL_VERIFIED', 'Manual Verified'),
                    ('SYNTHETIC', 'Synthetic'),
                    ('UNVERIFIED', 'Unverified'),
                    ('CORRECTED', 'Corrected'),
                ], db_index=True, default='UNVERIFIED', max_length=32,
            ),
        ),
    ]
