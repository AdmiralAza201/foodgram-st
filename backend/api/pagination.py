from rest_framework.pagination import PageNumberPagination

from core.constants import DEFAULT_PAGE_SIZE


class LimitPageNumberPagination(PageNumberPagination):
    page_size = DEFAULT_PAGE_SIZE
    page_size_query_param = "limit"
    max_page_size = DEFAULT_PAGE_SIZE
