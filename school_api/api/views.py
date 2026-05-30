from django.shortcuts import render
import requests

BASE_URL = "https://www.spsghy.co.in/api"
HEADERS = {"User-Agent": "Mozilla/5.0"}


def dashboard(request):
    session = request.GET.get('session', '20262027')

    selected_class = request.GET.get('class')
    selected_sec = request.GET.get('sec')
    selected_student = request.GET.get('student')
    selected_quarters = request.GET.getlist('quarter')

    class_data = []
    unique_classes = []
    students = []
    fee_data = None
    error = None

   
    # 1️ Get Class & Section
    
    try:
        res = requests.get(
            f"{BASE_URL}/studentinfo/get_class_sec.php",
            params={"session": session},
            headers=HEADERS
        )

        if res.status_code == 200:
            data = res.json()
            class_data = data.get("data", [])

            # Unique classes
            seen = set()
            for item in class_data:
                cls = item.get("CLASS")
                if cls and cls not in seen:
                    seen.add(cls)
                    unique_classes.append(cls)
        else:
            error = "Failed to fetch class data"

    except Exception:
        error = "Failed to load class data"

  
    # 2️ Get Students
  
    if selected_class and selected_sec:
        try:
            res = requests.get(
                f"{BASE_URL}/studentinfo/get_students.php",
                params={
                    "session": session,
                    "class": selected_class,
                    "sec": selected_sec
                },
                headers=HEADERS
            )

            if res.status_code == 200:
                students = res.json().get("data", [])

                if not students:
                    error = "No students found"
            else:
                error = "Failed to fetch students"

        except Exception:
            error = "Failed to load students"

    # 3️ Get Fee Details
   
    if selected_student:
        try:
            res = requests.get(
                f"{BASE_URL}/fees/fee-api.php",
                params={
                    "CODE": selected_student,
                    "Session": session
                },
                headers=HEADERS
            )

            if res.status_code == 200:
                data = res.json()

                grouped_fees = {
                    "Quarter1": [],
                    "Quarter2": [],
                    "Quarter3": [],
                    "Quarter4": []
                }

                for fee in data.get("pending_fees", []):
                    q = fee.get("FEETYPE")
                    if q in grouped_fees:
                        grouped_fees[q].append(fee)

                order = ["Quarter1", "Quarter2", "Quarter3", "Quarter4"]
                first_pending = next((q for q in order if grouped_fees[q]), None)

                if selected_quarters:
                    if first_pending and first_pending not in selected_quarters:
                        error = f"Pay {first_pending} first!"
                    else:
                        filtered_fees = {}
                        total = 0

                        for q in selected_quarters:
                            fees = grouped_fees.get(q, [])
                            filtered_fees[q] = fees

                            for f in fees:
                                total += int(f.get("total_fee", 0))

                        outstanding = int(data.get("outstandingfee", 0))
                        latefee = int(data.get("latefee", 0))

                        fee_data = {
                            "student": data.get("student_details"),
                            "fees": filtered_fees,
                            "final_total": total + outstanding + latefee,
                            "outstanding": outstanding,
                            "latefee": latefee
                        }

        except Exception:
            error = "Failed to load fee data"

    return render(request, "dashboard.html", {
        "session": session,
        "class_data": class_data,
        "unique_classes": unique_classes,
        "students": students,
        "fee_data": fee_data,
        "selected_class": selected_class,
        "selected_sec": selected_sec,
        "selected_student": selected_student,
        "selected_quarters": selected_quarters,
        "error": error
    })