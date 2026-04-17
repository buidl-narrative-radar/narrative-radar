def render_template(state: dict) -> str:
    return (
        f"{state['asset_key']}는 현재 {state['mood_label']} 상태이며, "
        f"crowd는 {state['playbook_label']} 전략을 보이고 있습니다. "
        f"리스크 요인은 {', '.join(state['risk_flags'])}입니다."
    )