from pathlib import Path
import json

def generate_patient_summary(final_report):
    lines=[]
    lines.append(
         f"Your medical report contains {final_report['total_tests']} tests."
    )
    if final_report["abnormal_count"]==0:
        lines.append("All results are within normal range.")
        return " ".join(lines)
    lines.append(
        f"{final_report['abnormal_count']} test(s) need attention.")
    
    for test in final_report["abnormal_tests"]:
        lines.append(
             f"- {test['test_name']}: {test['value']} {test['unit']} "
            f"({test['status']}). {test['reason']}"
        )
    lines.append("Please consult your doctor for medical advice.")
    
    return " ".join(lines)

def build_final_report(report_id, extracted_data):
    abnormal_tests = [
        t for t in extracted_data
        if t["status"] in ("low", "high")
    ]

    report={
        "report_id": report_id,
        "total_tests": len(extracted_data),
        "abnormal_count": len(abnormal_tests),
        "abnormal_tests": abnormal_tests,
        "tests": extracted_data
    }
    report["patient_summary"]=generate_patient_summary(report)

    return report




def export_report_json(report_id, extracted_data, output_dir="outputs"):

    
    Path(output_dir).mkdir(exist_ok=True)
    out_path = Path(output_dir) / f"{report_id}_extracted.json"

    final_report = build_final_report(
    report_id=report_id,
    extracted_data=extracted_data)

    Path("outputs").mkdir(exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(final_report, f, indent=2)

    print(f"Saved structured report to {out_path}")



    
# export_report_json(
#     report_id="cbc_report_001",
#     extracted_data=extracted_data
# )

# final_report = build_final_report(
#     report_id="cbc_report_001",
#     extracted_data=extracted_data
# )