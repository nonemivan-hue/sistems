"""
Data models and business logic for transport cards system.
"""
from app.storage import (
    load_all, save_all, find_one, find_many, insert, update, delete, get_next_number
)
from datetime import datetime


# ============== CONSTANTS ==============
CARD_STATUSES = {
    "ready_to_print": "Готова к печати",
    "ready_to_issue": "Готова к выдаче",
    "issued": "Выдана",
    "defect": "Брак",
    "transferred_region": "Передана в другой регион",
    "written_off": "Списана",
    "": ""
}

DOCUMENT_TYPES = {
    "receipt": "Прием карт",
    "defect": "Брак",
    "print": "Печать карт",
    "issue": "Выдача карт",
    "transfer_mfc": "Передача в МФЦ",
    "transfer_region": "Передача в другой регион",
    "return_mfc": "Возврат из МФЦ",
    "writeoff": "Списание карт",
    "inventory": "Инвентаризация"
}

REPORT_STATUSES = [
    "ready_to_print",
    "ready_to_issue", 
    "issued",
    "defect",
    "transferred_region"
]


# ============== HELPERS ==============
def now_iso():
    return datetime.now().isoformat()


def log_action(user_id, action, details=""):
    insert("action_log", {
        "user_id": user_id,
        "action": action,
        "details": details,
        "timestamp": now_iso()
    })


# ============== CARD REFERENCE ==============
def get_cards(filters=None, sort_by=None, exclude_written_off=False):
    cards = load_all("cards")
    if exclude_written_off:
        cards = [c for c in cards if c.get("status") != "written_off"]
    if filters:
        for key, value in filters.items():
            if value:
                cards = [c for c in cards if str(c.get(key, "")).lower().find(str(value).lower()) >= 0]
    if sort_by:
        cards = sorted(cards, key=lambda x: x.get(sort_by, ""))
    return cards


def get_card_by_number(number):
    return find_one("cards", lambda c: c.get("card_number") == number)


def create_or_update_card(card_data, user_id=None):
    existing = get_card_by_number(card_data.get("card_number"))
    if existing:
        updates = {k: v for k, v in card_data.items() if k not in ["id", "created_at"]}
        updates["updated_at"] = now_iso()
        result = update("cards", lambda c: c.get("id") == existing["id"], updates)
        if user_id:
            log_action(user_id, "UPDATE_CARD", f"Updated card {card_data.get('card_number')}")
        return result
    else:
        result = insert("cards", card_data)
        if user_id:
            log_action(user_id, "CREATE_CARD", f"Created card {card_data.get('card_number')}")
        return result


# ============== CARD TYPES ==============
def get_card_types():
    return load_all("card_types")


def get_card_type_by_id(ct_id):
    return find_one("card_types", lambda c: c.get("id") == ct_id)


def get_card_type_by_name(name):
    return find_one("card_types", lambda c: c.get("name") == name)


# ============== OWNERS ==============
def get_owners():
    return load_all("owners")


def get_owner_by_id(o_id):
    return find_one("owners", lambda o: o.get("id") == o_id)


def get_owner_by_name(full_name):
    return find_one("owners", lambda o: o.get("full_name") == full_name)


def create_owner_if_not_exists(full_name, user_id=None):
    existing = get_owner_by_name(full_name)
    if existing:
        return existing
    result = insert("owners", {"full_name": full_name})
    if user_id:
        log_action(user_id, "CREATE_OWNER", f"Created owner {full_name}")
    return result


# ============== APPLICANTS ==============
def get_applicants():
    return load_all("applicants")


def get_applicant_by_id(a_id):
    return find_one("applicants", lambda a: a.get("id") == a_id)


def get_applicant_by_name(full_name):
    return find_one("applicants", lambda a: a.get("full_name") == full_name)


def create_applicant_if_not_exists(full_name, user_id=None):
    existing = get_applicant_by_name(full_name)
    if existing:
        return existing
    result = insert("applicants", {"full_name": full_name})
    if user_id:
        log_action(user_id, "CREATE_APPLICANT", f"Created applicant {full_name}")
    return result


# ============== ORGANIZATIONS ==============
def get_organizations():
    return load_all("organizations")


def get_organization_by_id(org_id):
    return find_one("organizations", lambda o: o.get("id") == org_id)


# ============== MFC ==============
def get_mfcs():
    return load_all("mfcs")


def get_mfc_by_id(mfc_id):
    return find_one("mfcs", lambda m: m.get("id") == mfc_id)


# ============== EMPLOYEES ==============
_active_sessions = {}

def get_employees():
    return load_all("employees")


def get_employee_by_id(e_id):
    return find_one("employees", lambda e: e.get("id") == e_id)


def get_employee_by_login(login):
    return find_one("employees", lambda e: e.get("login") == login)


def register_session(user_id, session_id):
    """Register an active user session."""
    from datetime import datetime
    _active_sessions[session_id] = {
        "user_id": user_id,
        "last_activity": datetime.now().isoformat()
    }


def unregister_session(session_id):
    """Unregister a user session."""
    if session_id in _active_sessions:
        del _active_sessions[session_id]


def update_session_activity(session_id):
    """Update last activity time for a session."""
    if session_id in _active_sessions:
        from datetime import datetime
        _active_sessions[session_id]["last_activity"] = datetime.now().isoformat()


def get_active_users():
    """Get list of currently active users."""
    from datetime import datetime, timedelta
    # Consider sessions active if they had activity in the last 15 minutes
    cutoff = (datetime.now() - timedelta(minutes=15)).isoformat()
    active_user_ids = set()
    for sess in _active_sessions.values():
        if sess.get("last_activity", "") > cutoff:
            active_user_ids.add(sess["user_id"])
    
    employees = get_employees()
    return [e for e in employees if e.get("id") in active_user_ids]


def check_permission(employee, resource, level="view"):
    """Check if employee has permission for resource at given level."""
    if "admin" in employee.get("roles", []):
        return True
    perms = employee.get("permissions", {})
    resource_perm = perms.get(resource, "")
    if level == "view":
        return resource_perm in ["view", "edit"]
    if level == "edit":
        return resource_perm == "edit"
    return False


# ============== DOCUMENTS ==============
def get_documents(doc_type=None, date_from=None, date_to=None):
    docs = load_all("documents")
    if doc_type:
        docs = [d for d in docs if d.get("doc_type") == doc_type]
    if date_from:
        docs = [d for d in docs if d.get("doc_date", "") >= date_from]
    if date_to:
        docs = [d for d in docs if d.get("doc_date", "") <= date_to]
    return sorted(docs, key=lambda x: x.get("doc_date", ""), reverse=True)


def get_document_by_id(doc_id):
    return find_one("documents", lambda d: d.get("id") == doc_id)


def delete_document(doc_id, user_id=None):
    doc = get_document_by_id(doc_id)
    if not doc:
        return False
    # Revert card statuses if needed
    if doc.get("status") == "posted":
        for line in doc.get("lines", []):
            card = get_card_by_number(line.get("card_number"))
            if card:
                # Simple revert - set to previous status or empty
                update("cards", lambda c: c.get("id") == card["id"],
                       {"status": "", "updated_at": now_iso()})
    delete("documents", lambda d: d.get("id") == doc_id)
    if user_id:
        log_action(user_id, "DELETE_DOC", f"Deleted document {doc.get('doc_number')}")
    return True


def post_document(doc_id, user_id=None):
    """Post a document - apply business logic and update card statuses."""
    doc = get_document_by_id(doc_id)
    if not doc or doc.get("status") == "posted":
        return False, "Документ не найден или уже проведен"

    errors = []
    doc_type = doc.get("doc_type")
    lines = doc.get("lines", [])

    for idx, line in enumerate(lines, 1):
        card_number = line.get("card_number")
        card = get_card_by_number(card_number)

        if doc_type == "receipt":
            # Прием карт
            if card and card.get("status") not in ["", "transferred_region"]:
                errors.append(f"Строка {idx}: Карта {card_number} уже существует со статусом '{CARD_STATUSES.get(card.get('status'), card.get('status'))}'")
            else:
                card_data = {
                    "card_number": card_number,
                    "card_type_id": line.get("card_type_id"),
                    "status": "ready_to_print",
                    "owner_id": "",
                    "applicant_id": ""
                }
                create_or_update_card(card_data, user_id)

        elif doc_type == "defect":
            # Брак
            if not card:
                errors.append(f"Строка {idx}: Карта {card_number} не зарегистрирована в системе")
            elif card.get("status") not in ["ready_to_print", "ready_to_issue"]:
                errors.append(f"Строка {idx}: Карта {card_number} имеет статус '{CARD_STATUSES.get(card.get('status'), card.get('status'))}'")
            else:
                update("cards", lambda c: c.get("id") == card["id"],
                       {"status": "defect", "updated_at": now_iso()})

        elif doc_type == "print":
            # Печать карт
            if not card:
                errors.append(f"Строка {idx}: Карта {card_number} не зарегистрирована в системе")
            elif card.get("status") != "ready_to_print":
                errors.append(f"Строка {idx}: Карта {card_number} имеет статус '{CARD_STATUSES.get(card.get('status'), card.get('status'))}'")
            else:
                # Create/update owner
                owner = create_owner_if_not_exists(line.get("owner_name", ""), user_id) if line.get("owner_name") else None
                updates = {
                    "status": "ready_to_issue",
                    "owner_id": owner["id"] if owner else card.get("owner_id", ""),
                    "updated_at": now_iso()
                }
                update("cards", lambda c: c.get("id") == card["id"], updates)

        elif doc_type == "issue":
            # Выдача карт
            if not card:
                errors.append(f"Строка {idx}: Карта {card_number} не числится в системе")
            elif card.get("status") != "ready_to_issue":
                errors.append(f"Строка {idx}: Карта {card_number} имеет статус '{CARD_STATUSES.get(card.get('status'), card.get('status'))}'")
            else:
                # Handle applicant
                card_type = get_card_type_by_id(card.get("card_type_id"))
                ct_name = card_type.get("name", "") if card_type else ""
                if ct_name == "Многодетные семьи" and line.get("applicant_name"):
                    applicant = create_applicant_if_not_exists(line.get("applicant_name"), user_id)
                    applicant_id = applicant["id"]
                else:
                    applicant_id = card.get("owner_id", "")

                update("cards", lambda c: c.get("id") == card["id"],
                       {"status": "issued", "applicant_id": applicant_id, "updated_at": now_iso()})

        elif doc_type == "transfer_mfc":
            # Передача в МФЦ
            if not card:
                errors.append(f"Строка {idx}: Карта {card_number} не числится в системе")
            elif card.get("status") != "ready_to_issue":
                errors.append(f"Строка {idx}: Карта {card_number} имеет статус '{CARD_STATUSES.get(card.get('status'), card.get('status'))}'")
            else:
                update("cards", lambda c: c.get("id") == card["id"],
                       {"status": "issued", "updated_at": now_iso()})

        elif doc_type == "transfer_region":
            # Передача в другой регион
            if not card:
                errors.append(f"Строка {idx}: Карта {card_number} не числится в системе")
            elif card.get("status") != "ready_to_print":
                errors.append(f"Строка {idx}: Карта {card_number} имеет статус '{CARD_STATUSES.get(card.get('status'), card.get('status'))}'")
            else:
                update("cards", lambda c: c.get("id") == card["id"],
                       {"status": "transferred_region", "updated_at": now_iso()})

        elif doc_type == "return_mfc":
            # Возврат из МФЦ
            if not card:
                errors.append(f"Строка {idx}: Карта {card_number} не числится в системе")
            elif card.get("status") != "issued":
                errors.append(f"Строка {idx}: Карта {card_number} имеет статус '{CARD_STATUSES.get(card.get('status'), card.get('status'))}'")
            else:
                update("cards", lambda c: c.get("id") == card["id"],
                       {"status": "ready_to_issue", "updated_at": now_iso()})

        elif doc_type == "writeoff":
            # Списание карт
            if not card:
                errors.append(f"Строка {idx}: Карта {card_number} не зарегистрирована в системе")
            else:
                update("cards", lambda c: c.get("id") == card["id"],
                       {"status": "written_off", "updated_at": now_iso()})

        elif doc_type == "inventory":
            # Инвентаризация - не меняет статусы карт, только фиксирует расхождения
            pass  # Логика обработки инвентаризации реализуется отдельно

    if errors:
        return False, "; ".join(errors)

    # Mark document as posted
    update("documents", lambda d: d.get("id") == doc_id,
           {"status": "posted", "posted_at": now_iso(), "posted_by": user_id})

    if user_id:
        log_action(user_id, "POST_DOC", f"Posted document {doc.get('doc_number')} ({doc_type})")

    return True, "Документ проведен успешно"


# ============== REPORTS ==============
def get_stock_report():
    """Report: stock of cards by type (ready_to_print and ready_to_issue)."""
    cards = load_all("cards")
    # Exclude written off cards from reports
    cards = [c for c in cards if c.get("status") != "written_off"]
    card_types = get_card_types()
    # Initialize counters for all card types
    result = {}
    for ct in card_types:
        result[ct["id"]] = {
            "card_type_name": ct.get("name", "Не указан"),
            "ready_to_print": 0,
            "ready_to_issue": 0
        }
    # Count cards
    for card in cards:
        ct_id = card.get("card_type_id", "")
        status = card.get("status", "")
        if ct_id in result and status in ("ready_to_print", "ready_to_issue"):
            result[ct_id][status] += 1
    # Build list, filter out rows with zero counts
    report = []
    for ct_id in sorted(result.keys(), key=lambda k: result[k]["card_type_name"]):
        row = result[ct_id]
        report.append(row)
    return report


def get_cards_report_as_of(date_str):
    """Report cards status as of specific date."""
    # For JSON storage, we use current state (simplified)
    # In SQL version, this would query historical state
    cards = load_all("cards")
    # Exclude written off cards from reports
    cards = [c for c in cards if c.get("status") != "written_off"]
    result = {}
    for card in cards:
        ct_id = card.get("card_type_id", "")
        status = card.get("status", "")
        key = (ct_id, status)
        result[key] = result.get(key, 0) + 1

    # Format for display
    report = []
    for (ct_id, status), count in result.items():
        ct = get_card_type_by_id(ct_id)
        report.append({
            "card_type_name": ct.get("name", "Не указан") if ct else "Не указан",
            "status": CARD_STATUSES.get(status, status),
            "status_code": status,
            "count": count
        })
    return report


def get_period_report(start_date, end_date):
    """Report for period: rows = card types, cols = print | issue+transfer_mfc."""
    docs = load_all("documents")

    # Collect print docs
    print_docs = [d for d in docs
                  if d.get("status") == "posted"
                  and start_date <= d.get("doc_date", "") <= end_date
                  and d.get("doc_type") == "print"]

    # Collect issue + transfer_mfc docs
    issue_docs = [d for d in docs
                  if d.get("status") == "posted"
                  and start_date <= d.get("doc_date", "") <= end_date
                  and d.get("doc_type") in ["issue", "transfer_mfc"]]

    # Group by card type
    print_counts = {}
    issue_counts = {}

    for doc in print_docs:
        for line in doc.get("lines", []):
            card = get_card_by_number(line.get("card_number"))
            if card:
                ct_id = card.get("card_type_id", "")
                print_counts[ct_id] = print_counts.get(ct_id, 0) + 1

    for doc in issue_docs:
        for line in doc.get("lines", []):
            card = get_card_by_number(line.get("card_number"))
            if card:
                ct_id = card.get("card_type_id", "")
                issue_counts[ct_id] = issue_counts.get(ct_id, 0) + 1

    # Build report: all card types that appear in either column
    all_ct_ids = set(list(print_counts.keys()) + list(issue_counts.keys()))
    report = []
    for ct_id in sorted(all_ct_ids):
        ct = get_card_type_by_id(ct_id)
        report.append({
            "card_type_name": ct.get("name", "Не указан") if ct else "Не указан",
            "print_count": print_counts.get(ct_id, 0),
            "issue_count": issue_counts.get(ct_id, 0)
        })
    return report


def get_period_report_detail(start_date, end_date):
    """Detailed period report: card numbers grouped by card type for print and issue docs."""
    docs = load_all("documents")

    print_docs = [d for d in docs
                  if d.get("status") == "posted"
                  and start_date <= d.get("doc_date", "") <= end_date
                  and d.get("doc_type") == "print"]

    issue_docs = [d for d in docs
                  if d.get("status") == "posted"
                  and start_date <= d.get("doc_date", "") <= end_date
                  and d.get("doc_type") in ["issue", "transfer_mfc"]]

    # Group card numbers by card type
    print_numbers = {}
    issue_numbers = {}

    for doc in print_docs:
        for line in doc.get("lines", []):
            card = get_card_by_number(line.get("card_number"))
            if card:
                ct_id = card.get("card_type_id", "")
                if ct_id not in print_numbers:
                    print_numbers[ct_id] = []
                print_numbers[ct_id].append(card.get("card_number", ""))

    for doc in issue_docs:
        for line in doc.get("lines", []):
            card = get_card_by_number(line.get("card_number"))
            if card:
                ct_id = card.get("card_type_id", "")
                if ct_id not in issue_numbers:
                    issue_numbers[ct_id] = []
                issue_numbers[ct_id].append(card.get("card_number", ""))

    # Build report with all card types
    all_ct_ids = set(list(print_numbers.keys()) + list(issue_numbers.keys()))
    card_types = get_card_types()
    ct_map = {ct["id"]: ct for ct in card_types}

    report = []
    for ct_id in sorted(all_ct_ids, key=lambda k: ct_map.get(k, {}).get("name", "")):
        ct = ct_map.get(ct_id)
        report.append({
            "card_type_name": ct.get("name", "Не указан") if ct else "Не указан",
            "print_name": ct.get("print_name", ct.get("name", "")) if ct else "",
            "print_numbers": sorted(print_numbers.get(ct_id, [])),
            "issue_numbers": sorted(issue_numbers.get(ct_id, []))
        })
    return report


def get_edo_report(start_date, end_date):
    """Report for EDO (print and defect documents)."""
    docs = load_all("documents")
    filtered = [d for d in docs
                if d.get("status") == "posted"
                and start_date <= d.get("doc_date", "") <= end_date
                and d.get("doc_type") in ["print", "defect"]]

    result = {}
    for doc in filtered:
        for line in doc.get("lines", []):
            card = get_card_by_number(line.get("card_number"))
            if card:
                ct_id = card.get("card_type_id", "")
                if ct_id not in result:
                    result[ct_id] = []
                result[ct_id].append(card.get("card_number"))

    report = []
    for ct_id, numbers in result.items():
        ct = get_card_type_by_id(ct_id)
        report.append({
            "card_type_name": ct.get("name", "Не указан") if ct else "Не указан",
            "numbers": ", ".join(sorted(numbers))
        })
    return report


def get_summary_report(start_date, end_date):
    """Summary report for period (print and defect)."""
    docs = load_all("documents")
    filtered = [d for d in docs
                if d.get("status") == "posted"
                and start_date <= d.get("doc_date", "") <= end_date
                and d.get("doc_type") in ["print", "defect"]]

    result = {}
    for doc in filtered:
        for line in doc.get("lines", []):
            card = get_card_by_number(line.get("card_number"))
            if card:
                ct_id = card.get("card_type_id", "")
                if ct_id not in result:
                    result[ct_id] = []
                result[ct_id].append(card.get("card_number"))

    report = []
    for ct_id, numbers in result.items():
        ct = get_card_type_by_id(ct_id)
        report.append({
            "card_type_name": ct.get("report_name", "") or ct.get("name", "Не указан") if ct else "Не указан",
            "print_name": ct.get("print_name", ct.get("name", "")) if ct else "",
            "numbers": sorted(numbers)
        })
    return report


def get_cards_as_of_report(as_of_date=None):
    """
    Report: карты на число.
    Rows = card types, columns = statuses, cells = count.
    Uses report_name from card_types.
    Excludes written off cards.
    """
    cards = load_all("cards")
    # Exclude written off cards from reports
    cards = [c for c in cards if c.get("status") != "written_off"]
    card_types = get_card_types()
    
    # Initialize matrix: {ct_id: {status: count}}
    result = {}
    for ct in card_types:
        ct_id = ct["id"]
        result[ct_id] = {"card_type_name": ct.get("report_name", "") or ct.get("name", "Не указан"), "total": 0}
        for status in REPORT_STATUSES:
            result[ct_id][status] = 0
    
    # Count cards
    for card in cards:
        ct_id = card.get("card_type_id", "")
        status = card.get("status", "")
        if ct_id in result and status in REPORT_STATUSES:
            result[ct_id][status] += 1
            result[ct_id]["total"] += 1
    
    # Build report list
    report = []
    for ct_id in sorted(result.keys(), key=lambda k: result[k]["card_type_name"]):
        report.append(result[ct_id])
    
    return report


def get_all_cards_report():
    """
    Report: Карты все.
    Rows = card types (Вид карты), columns = statuses (Статус карты), cells = count.
    Includes all cards regardless of status (including written_off).
    Returns: (report_list, statuses_list)
    """
    cards = load_all("cards")
    card_types = get_card_types()
    
    # Get all unique statuses from cards
    all_statuses = set()
    for card in cards:
        status = card.get("status", "")
        if status:
            all_statuses.add(status)
    
    statuses_list = sorted(list(all_statuses))
    
    # Initialize matrix: {ct_id: {status: count}}
    result = {}
    for ct in card_types:
        ct_id = ct["id"]
        result[ct_id] = {"card_type_name": ct.get("name", "Не указан"), "total": 0}
        for status in all_statuses:
            result[ct_id][status] = 0
    
    # Count cards
    for card in cards:
        ct_id = card.get("card_type_id", "")
        status = card.get("status", "")
        if ct_id in result and status:
            result[ct_id][status] += 1
            result[ct_id]["total"] += 1
    
    # Build report list
    report = []
    for ct_id in sorted(result.keys(), key=lambda k: result[k]["card_type_name"]):
        report.append(result[ct_id])
    
    return report, statuses_list


def get_demand_analysis_report(start_date, end_date, days_forecast):
    """
    Report: Анализ потребности.
    Rows = card types (Вид карты из справочника, поле name).
    Columns: Остаток, Печать (сумма за период), Остаток в днях, Необходимое кол-во на N дней.
    
    Остаток = карты со статусами ready_to_print и ready_to_issue.
    Печать = сумма карт из документов "Печать карт" за период.
    Остаток в днях = Остаток / (Печать за период / количество дней в периоде).
    Необходимое кол-во на N дней = (Печать за период / количество дней в периоде) * N дней.
    """
    from datetime import datetime
    
    cards = load_all("cards")
    card_types = get_card_types()
    docs = load_all("documents")
    
    # Calculate period length in days
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        period_days = max((end_dt - start_dt).days + 1, 1)
    except:
        period_days = 1
    
    # Calculate current stock (ready_to_print + ready_to_issue) by card type
    # Exclude written off cards
    cards = [c for c in cards if c.get("status") != "written_off"]
    stock_counts = {}
    for ct in card_types:
        stock_counts[ct["id"]] = 0
    
    for card in cards:
        ct_id = card.get("card_type_id", "")
        status = card.get("status", "")
        if status in ["ready_to_print", "ready_to_issue"] and ct_id in stock_counts:
            stock_counts[ct_id] += 1
    
    # Calculate print counts for the period by card type
    print_docs = [d for d in docs
                  if d.get("status") == "posted"
                  and start_date <= d.get("doc_date", "") <= end_date
                  and d.get("doc_type") == "print"]
    
    print_counts = {}
    for ct in card_types:
        print_counts[ct["id"]] = 0
    
    for doc in print_docs:
        for line in doc.get("lines", []):
            card = get_card_by_number(line.get("card_number"))
            if card:
                ct_id = card.get("card_type_id", "")
                if ct_id in print_counts:
                    print_counts[ct_id] += 1
    
    # Build report
    report = []
    for ct in card_types:
        ct_id = ct["id"]
        ct_name = ct.get("name", "Не указан")
        stock = stock_counts[ct_id]
        printed = print_counts[ct_id]
        
        # Average daily print
        avg_daily_print = printed / period_days if period_days > 0 else 0
        
        # Days of stock remaining
        days_remaining = round(stock / avg_daily_print, 1) if avg_daily_print > 0 else None
        
        # Required quantity for forecast days
        required_qty = round(avg_daily_print * days_forecast)
        
        report.append({
            "card_type_name": ct_name,
            "stock": stock,
            "printed": printed,
            "days_remaining": days_remaining,
            "required_qty": required_qty
        })
    
    # Sort by card type name
    report.sort(key=lambda x: x["card_type_name"])
    
    return report, period_days


# ============== INVENTORY FUNCTIONS ==============
def get_inventory_documents(date_from=None, date_to=None):
    """Get all inventory documents."""
    docs = get_documents(doc_type="inventory", date_from=date_from, date_to=date_to)
    return docs


def get_inventory_by_id(inv_id):
    """Get inventory document by ID."""
    return get_document_by_id(inv_id)


def create_inventory(doc_data, user_id=None):
    """Create inventory document with header and tab data."""
    doc = insert("documents", {
        "doc_type": "inventory",
        "doc_number": doc_data.get("doc_number") or get_next_number("ИНВ"),
        "doc_date": doc_data.get("doc_date"),
        "order_number": doc_data.get("order_number", ""),
        "order_date": doc_data.get("order_date", ""),
        "chairman_id": doc_data.get("chairman_id", ""),
        "committee_ids": doc_data.get("committee_ids", []),
        "card_status_filter": doc_data.get("card_status_filter", ""),
        "card_type_filter": doc_data.get("card_type_filter", ""),
        "accounting_lines": doc_data.get("accounting_lines", []),
        "actual_lines": doc_data.get("actual_lines", []),
        "discrepancy_lines": doc_data.get("discrepancy_lines", []),
        "status": "draft",
        "created_by": user_id,
        "created_at": now_iso()
    })
    if user_id:
        log_action(user_id, "CREATE_INVENTORY", f"Created inventory {doc.get('doc_number')}")
    return doc


def update_inventory(inv_id, doc_data, user_id=None):
    """Update inventory document."""
    updates = {
        "doc_number": doc_data.get("doc_number"),
        "doc_date": doc_data.get("doc_date"),
        "order_number": doc_data.get("order_number", ""),
        "order_date": doc_data.get("order_date", ""),
        "chairman_id": doc_data.get("chairman_id", ""),
        "committee_ids": doc_data.get("committee_ids", []),
        "card_status_filter": doc_data.get("card_status_filter", ""),
        "card_type_filter": doc_data.get("card_type_filter", ""),
        "accounting_lines": doc_data.get("accounting_lines", []),
        "actual_lines": doc_data.get("actual_lines", []),
        "discrepancy_lines": doc_data.get("discrepancy_lines", []),
        "updated_at": now_iso()
    }
    result = update("documents", lambda d: d.get("id") == inv_id, updates)
    if user_id:
        log_action(user_id, "UPDATE_INVENTORY", f"Updated inventory {doc_data.get('doc_number')}")
    return result


def calculate_inventory_discrepancies(accounting_lines, actual_lines):
    """
    Compare accounting and actual lines to find discrepancies.
    Returns list of discrepancy records.
    """
    # Build lookup maps by card_number
    acct_map = {line.get("card_number"): line for line in accounting_lines}
    actual_map = {line.get("card_number"): line for line in actual_lines}
    
    discrepancies = []
    all_cards = set(acct_map.keys()) | set(actual_map.keys())
    
    idx = 1
    for card_num in sorted(all_cards):
        acct_line = acct_map.get(card_num)
        actual_line = actual_map.get(card_num)
        
        if acct_line and not actual_line:
            # Недостача - есть в учете, но нет по факту
            discrepancies.append({
                "line_no": idx,
                "card_number": card_num,
                "card_type_id": acct_line.get("card_type_id"),
                "card_type_name": acct_line.get("card_type_name"),
                "status": acct_line.get("status"),
                "surplus": False,
                "shortage": True
            })
        elif actual_line and not acct_line:
            # Излишек - есть по факту, но нет в учете
            discrepancies.append({
                "line_no": idx,
                "card_number": card_num,
                "card_type_id": actual_line.get("card_type_id"),
                "card_type_name": actual_line.get("card_type_name"),
                "status": actual_line.get("status"),
                "surplus": True,
                "shortage": False
            })
        idx += 1
    
    return discrepancies


def get_cards_for_inventory(status_filter=None, type_filter=None):
    """
    Get cards for inventory based on filters.
    If no filters, default to ready_to_print and ready_to_issue statuses.
    Excludes written_off cards.
    """
    cards = load_all("cards")
    # Always exclude written off cards from inventory selection
    cards = [c for c in cards if c.get("status") != "written_off"]
    
    # Apply status filter
    if status_filter:
        cards = [c for c in cards if c.get("status") == status_filter]
    else:
        # Default: include ready_to_print and ready_to_issue
        cards = [c for c in cards if c.get("status") in ["ready_to_print", "ready_to_issue"]]
    
    # Apply type filter
    if type_filter:
        cards = [c for c in cards if c.get("card_type_id") == type_filter]
    
    # Enrich with card type info
    ct_map = {ct["id"]: ct for ct in get_card_types()}
    result = []
    for c in cards:
        ct = ct_map.get(c.get("card_type_id", ""), {})
        result.append({
            "card_number": c.get("card_number"),
            "card_type_id": c.get("card_type_id"),
            "card_type_name": ct.get("name", ""),
            "status": c.get("status"),
            "status_name": CARD_STATUSES.get(c.get("status"), "")
        })
    
    return result


def create_docs_from_inventory(inv_id, user_id=None):
    """
    Create documents from inventory results:
    - Writeoff for shortage with status ready_to_print
    - Receipt for surplus
    - Issue for shortage with status ready_to_issue
    Returns list of created document IDs.
    """
    inv = get_inventory_by_id(inv_id)
    if not inv:
        return []
    
    created_docs = []
    discrepancies = inv.get("discrepancy_lines", [])
    
    # Group by action type
    writeoff_cards = []  # shortage + ready_to_print
    issue_cards = []     # shortage + ready_to_issue  
    receipt_cards = []   # surplus
    
    for disc in discrepancies:
        card_num = disc.get("card_number")
        is_shortage = disc.get("shortage", False)
        is_surplus = disc.get("surplus", False)
        status = disc.get("status", "")
        
        if is_shortage and status == "ready_to_print":
            writeoff_cards.append(disc)
        elif is_shortage and status == "ready_to_issue":
            issue_cards.append(disc)
        elif is_surplus:
            receipt_cards.append(disc)
    
    # Create writeoff document
    if writeoff_cards:
        lines = [{"line_no": idx+1, "card_number": c.get("card_number"), 
                  "card_type_id": c.get("card_type_id")} 
                 for idx, c in enumerate(writeoff_cards)]
        doc = insert("documents", {
            "doc_type": "writeoff",
            "doc_number": get_next_number("СП"),
            "doc_date": datetime.now().strftime("%Y-%m-%d"),
            "lines": lines,
            "status": "draft",
            "created_by": user_id,
            "created_at": now_iso(),
            "source_inventory_id": inv_id
        })
        created_docs.append(doc["id"])
    
    # Create issue document
    if issue_cards:
        lines = [{"line_no": idx+1, "card_number": c.get("card_number"),
                  "card_type_id": c.get("card_type_id")}
                 for idx, c in enumerate(issue_cards)]
        doc = insert("documents", {
            "doc_type": "issue",
            "doc_number": get_next_number("Выд"),
            "doc_date": datetime.now().strftime("%Y-%m-%d"),
            "lines": lines,
            "status": "draft",
            "created_by": user_id,
            "created_at": now_iso(),
            "source_inventory_id": inv_id
        })
        created_docs.append(doc["id"])
    
    # Create receipt document
    if receipt_cards:
        lines = [{"line_no": idx+1, "card_number": c.get("card_number"),
                  "card_type_id": c.get("card_type_id")}
                 for idx, c in enumerate(receipt_cards)]
        doc = insert("documents", {
            "doc_type": "receipt",
            "doc_number": get_next_number("ПР"),
            "doc_date": datetime.now().strftime("%Y-%m-%d"),
            "lines": lines,
            "status": "draft",
            "created_by": user_id,
            "created_at": now_iso(),
            "source_inventory_id": inv_id
        })
        created_docs.append(doc["id"])
    
    return created_docs


# ============== WORK BLOCKS (Блоки для работы учреждения) ==============
def get_work_blocks():
    """Список всех блоков работы (Карты, Приказы и др.), отсортированных по порядку."""
    blocks = load_all("work_blocks")
    return sorted(blocks, key=lambda b: (b.get("order", 0), b.get("name", "")))


def get_work_block_by_id(block_id):
    return find_one("work_blocks", lambda b: b.get("id") == block_id)


def create_work_block(name, url, icon="bi-box", order=0, allowed_logins=None):
    """Создать блок работы. name - название, url - путь/ссылка к блоку,
    allowed_logins - список логинов сотрудников, которым разрешен вход в блок
    (пустой список / None = всем)."""
    return insert("work_blocks", {
        "name": name,
        "url": url,
        "icon": icon or "bi-box",
        "order": order,
        "allowed_logins": allowed_logins or [],
    })


def update_work_block(block_id, updates):
    return update("work_blocks", lambda b: b.get("id") == block_id, updates)


def delete_work_block(block_id):
    delete("work_blocks", lambda b: b.get("id") == block_id)


def can_access_block(employee, block):
    """Проверить доступ сотрудника к блоку.
    Администратор имеет доступ всегда; иначе логин сотрудника должен быть
    в списке разрешенных (пустой список = доступ для всех)."""
    if not employee:
        return False
    if "admin" in employee.get("roles", []):
        return True
    allowed = block.get("allowed_logins") or []
    if not allowed:
        return True
    return employee.get("login") in allowed


def get_visible_blocks(employee):
    """Блоки, доступные данному сотруднику."""
    return [b for b in get_work_blocks() if can_access_block(employee, b)]
