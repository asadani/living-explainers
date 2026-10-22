def preview_request(user, document, renderer):
    if not user or not document:
        raise ValueError("user and document are required")
    decision = authorize_preview(user, document)
    return renderer.preview(document) if decision.allowed else None
