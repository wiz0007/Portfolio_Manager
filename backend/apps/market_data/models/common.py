from django.db import models


class CrossDbQuerySet(models.QuerySet):
    """
    Transparently maps cross-database conceptual relations (like instrument, user)
    to scalar UUID foreign keys (instrument_id, user_id, recorded_by_id, published_by_id)
    across filter, exclude, get, create, order_by, select_related, etc.
    """

    def _transform_q(self, q):
        if not isinstance(q, models.Q):
            return q
        new_children = []
        for child in q.children:
            if isinstance(child, tuple):
                k, v = child
                if k == 'instrument':
                    new_children.append(('instrument_id', getattr(v, 'id', v)))
                elif k.startswith('instrument__'):
                    suffix = k[len('instrument__'):]
                    if suffix in ('id', 'pk'):
                        new_children.append(('instrument_id', getattr(v, 'id', v)))
                    else:
                        new_children.append(('instrument_id__' + suffix, getattr(v, 'id', v)))
                elif k == 'user':
                    new_children.append(('user_id', getattr(v, 'id', v)))
                elif k.startswith('user__'):
                    suffix = k[len('user__'):]
                    if suffix in ('id', 'pk'):
                        new_children.append(('user_id', getattr(v, 'id', v)))
                    else:
                        new_children.append(('user_id__' + suffix, getattr(v, 'id', v)))
                elif k == 'recorded_by':
                    new_children.append(('recorded_by_id', getattr(v, 'id', v)))
                elif k == 'published_by':
                    new_children.append(('published_by_id', getattr(v, 'id', v)))
                else:
                    new_children.append((k, v))
            elif isinstance(child, models.Q):
                new_children.append(self._transform_q(child))
            else:
                new_children.append(child)
        q.children = new_children
        return q

    def _transform_kwargs(self, kwargs):
        new_kwargs = {}
        for k, v in kwargs.items():
            if k == 'instrument':
                new_kwargs['instrument_id'] = getattr(v, 'id', v)
            elif k.startswith('instrument__'):
                suffix = k[len('instrument__'):]
                if suffix in ('id', 'pk'):
                    new_kwargs['instrument_id'] = getattr(v, 'id', v)
                else:
                    new_kwargs['instrument_id__' + suffix] = getattr(v, 'id', v)
            elif k == 'user':
                new_kwargs['user_id'] = getattr(v, 'id', v)
            elif k.startswith('user__'):
                suffix = k[len('user__'):]
                if suffix in ('id', 'pk'):
                    new_kwargs['user_id'] = getattr(v, 'id', v)
                else:
                    new_kwargs['user_id__' + suffix] = getattr(v, 'id', v)
            elif k == 'recorded_by':
                new_kwargs['recorded_by_id'] = getattr(v, 'id', v)
            elif k == 'published_by':
                new_kwargs['published_by_id'] = getattr(v, 'id', v)
            else:
                new_kwargs[k] = v
        return new_kwargs

    def filter(self, *args, **kwargs):
        new_args = [self._transform_q(a) for a in args]
        return super().filter(*new_args, **self._transform_kwargs(kwargs))

    def exclude(self, *args, **kwargs):
        new_args = [self._transform_q(a) for a in args]
        return super().exclude(*new_args, **self._transform_kwargs(kwargs))

    def get(self, *args, **kwargs):
        new_args = [self._transform_q(a) for a in args]
        return super().get(*new_args, **self._transform_kwargs(kwargs))

    def get_or_create(self, defaults=None, **kwargs):
        if defaults:
            defaults = self._transform_kwargs(defaults)
        return super().get_or_create(defaults=defaults, **self._transform_kwargs(kwargs))

    def update_or_create(self, defaults=None, **kwargs):
        if defaults:
            defaults = self._transform_kwargs(defaults)
        return super().update_or_create(defaults=defaults, **self._transform_kwargs(kwargs))

    def create(self, **kwargs):
        return super().create(**self._transform_kwargs(kwargs))

    def order_by(self, *field_names):
        new_names = []
        for name in field_names:
            if name == 'instrument':
                new_names.append('instrument_id')
            elif name == '-instrument':
                new_names.append('-instrument_id')
            elif name == 'user':
                new_names.append('user_id')
            elif name == '-user':
                new_names.append('-user_id')
            else:
                new_names.append(name)
        return super().order_by(*new_names)

    def select_related(self, *fields):
        cross_db_fields = {'instrument', 'user', 'recorded_by', 'published_by'}
        filtered_fields = [f for f in fields if f not in cross_db_fields]
        return super().select_related(*filtered_fields) if filtered_fields else self

    def prefetch_related(self, *lookups):
        cross_db_fields = {'instrument', 'user', 'recorded_by', 'published_by'}
        filtered_lookups = [f for f in lookups if f not in cross_db_fields]
        return super().prefetch_related(*filtered_lookups) if filtered_lookups else self

    def values(self, *fields, **expressions):
        new_fields = ['instrument_id' if f == 'instrument' else ('user_id' if f == 'user' else f) for f in fields]
        return super().values(*new_fields, **expressions)

    def values_list(self, *fields, **expressions):
        new_fields = ['instrument_id' if f == 'instrument' else ('user_id' if f == 'user' else f) for f in fields]
        return super().values_list(*new_fields, **expressions)
