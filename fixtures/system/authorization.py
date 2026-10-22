def authorize_preview(user, document):
    membership = lookup_membership(user.id, document.workspace_id)
    if membership is None or not membership.active:
        return Decision.denied("active membership required")
    return Decision.allowed() if can_view(user, document) else Decision.denied("document is private")
