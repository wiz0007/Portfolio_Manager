import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('assets', '0005_investmenttransaction_gross_amount_and_more')]

    operations = [
        migrations.AlterField(
            model_name='investment', name='portfolio',
            field=models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.PROTECT, related_name='investments', to='portfolios.portfolio'),
        ),
        migrations.AlterField(
            model_name='investmenttransaction', name='investment',
            field=models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.PROTECT, related_name='transactions', to='assets.investment'),
        ),
        migrations.AlterField(
            model_name='investmenttransaction', name='portfolio',
            field=models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.PROTECT, related_name='investment_transactions', to='portfolios.portfolio'),
        ),
        migrations.AlterField(
            model_name='investmenttransaction', name='user',
            field=models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.PROTECT, related_name='investment_transactions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='investmentvaluation', name='investment',
            field=models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.PROTECT, related_name='valuations', to='assets.investment'),
        ),
    ]
