import frappe


def get_context(context):
    context.no_cache = 1
    context.title = "Questionnaire Pré-audit | Amoaman & Associés"
    context.description = (
        "Répondez à 15 questions pour évaluer la conformité de votre entreprise "
        "à la loi ivoirienne sur la protection des données personnelles."
    )
    return context
