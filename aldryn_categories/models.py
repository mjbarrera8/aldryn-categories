# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.db import IntegrityError, models
from django.template.defaultfilters import slugify as default_slugify
from django.utils.translation import (
    ugettext_lazy as _,
    # get_language,
)

from parler.models import TranslatableModel, TranslatedFields
# from parler.utils.context import switch_language
from parler.managers import TranslatableManager

from treebeard.ns_tree import NS_Node, NS_NodeManager


class CategoryManager(NS_NodeManager, TranslatableManager):
    pass


#
# NOTE: I would have preferred to make this a base class "CategoryBase" which
# is Abstract, then subclass it as a concreate Category class. But, Parler
# cannot be applied to an Abstract class.
#
# TODO: At some point, consider an approach like this:
#     https://gist.github.com/GaretJax/7c7a9acc055c05c65041
#
class Category(TranslatableModel, NS_Node):
    """
    A category is hierarchical. The structure is implemented with django-
    treebeard's Nested Sets trees, which has the performance characteristics
    we're after, namely: fast reads at the expense of write-speed.
    """
    node_order_by = ['name', ]

    translations = TranslatedFields(
        name=models.CharField(
            _('name'),
            blank=False,
            default='',
            max_length=255,
        ),
        slug=models.SlugField(
            _('slug'),
            help_text=_('Provide a “slug” or leave blank for an automatically '
                        'generated one.'),
            max_length=255,
        )
    )

    objects = CategoryManager()

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')

    def slugify(self, category, i=None):
        slug = default_slugify(category)
        if i is not None:
            slug += "_%d" % i
        return slug

    def save(self, *args, **kwargs):
        if not self.pk and not self.slug:
            self.slug = self.slugify(self.name)
            try:
                return super(Category, self).save(self, *args, **kwargs)
            except IntegrityError:
                pass

            # Find similar slugs
            slugs = set(Category.objects
                                .filter(slug__startswith=self.slug)
                                .values_list('slug', flat=True))
            i = 1
            while True:
                slug = self.slugify(self.name, i)
                if slug not in slugs:
                    self.slug = slug
                    return super(Category, self).save(self, *args, **kwargs)
                i += 1
        else:
            return super(Category, self).save(self, *args, **kwargs)