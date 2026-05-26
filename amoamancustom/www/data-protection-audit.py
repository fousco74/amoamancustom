import frappe


def get_context(context):
    context.no_cache = 1
    context.title = "Pré-audit de conformité — Protection des données personnelles | Amoaman & Associés"
    context.description = (
        "Diagnostiquez gratuitement la conformité de votre entreprise "
        "à la loi ivoirienne sur la protection des données personnelles. "
        "15 questions, rapport personnalisé."
    )
    return context
