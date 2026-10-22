def render_preview(document, renderer):
    try:
        return renderer.render(document.content)
    except RendererTimeout:
        return PreviewUnavailable(retryable=True)
