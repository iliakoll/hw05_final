from django.core.paginator import Paginator


LAST_NUM_POSTS: int = 10


def get_paginator(request, set_posts):

    paginator = Paginator(set_posts, LAST_NUM_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return page_obj
