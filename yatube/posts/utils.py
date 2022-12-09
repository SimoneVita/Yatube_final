from django.core.paginator import Paginator

from .constants import POSTS_PER_PAGE


def pagination(request, value):
    paginator = Paginator(value, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
