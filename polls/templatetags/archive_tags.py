from django import template


register = template.Library()


@register.inclusion_tag("polls/partials/archive_article_card.html")
def archive_article_card(
    article,
    headline_level="h2",
    headline_url=None,
    link_to_article_anchor=False,
    show_author=True,
    content_mode="none",
):
    return {
        "article": article,
        "headline_level": headline_level,
        "headline_url": headline_url,
        "link_to_article_anchor": link_to_article_anchor,
        "show_author": show_author,
        "content_mode": content_mode,
    }
