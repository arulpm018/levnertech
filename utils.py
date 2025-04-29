from typing import Dict, Any, List

# Thresholds untuk mapping skor ke verdict
COMPLIED_THRESHOLD = 0.85
MINOR_NC_THRESHOLD = 0.7
MAJOR_NC_THRESHOLD = 0.6


def score_to_verdict(relevance: float, completeness: float) -> str:
    """
    Map relevance & completeness scores ke verdict.

    - Complied: both >= COMPLIED_THRESHOLD
    - Minor NC: both >= MINOR_NC_THRESHOLD
    - Opportunity for Improvement: one >= MINOR_NC_THRESHOLD
    - Major NC: otherwise
    """
    if relevance >= COMPLIED_THRESHOLD and completeness >= COMPLIED_THRESHOLD:
        return "Complied"
    if relevance < MAJOR_NC_THRESHOLD or completeness < MAJOR_NC_THRESHOLD:
        return "Major NC"
    if relevance >= MINOR_NC_THRESHOLD and completeness >= MINOR_NC_THRESHOLD:
        return "Minor NC"
    return "Opportunity for Improvement"


def generate_gap_analysis(clause_id: str, verdict: str, details: Dict[str, Any]) -> Dict[str, Any]:
    """
    Buat analisis gap untuk satu klausul.
    """
    return {
        "clause": clause_id,
        "verdict": verdict,
        "details": details
    }


def generate_recommendations(analysis: Dict[str, Any]) -> List[str]:
    """
    Saran perbaikan berdasarkan verdict.
    """
    v = analysis.get("verdict")
    recs = []
    if v == "Complied":
        recs.append("Pertahankan praktik yang telah berjalan dengan baik.")
    elif v == "Minor NC":
        recs.append("Perbaiki detail yang kurang untuk memenuhi standar penuh.")
        recs.append("Tinjau kembali dokumentasi dan lengkapi bagian yang belum memadai.")
    elif v == "Opportunity for Improvement":
        recs.append("Pertimbangkan untuk meningkatkan proses meski sudah memenuhi syarat minimal.")
        recs.append("Tuliskan prosedur lebih rinci untuk meningkatkan konsistensi implementasi.")
    else:  # Major NC
        recs.append("Segera implementasikan proses sesuai klausul yang belum ada.")
        recs.append("Susun dan dokumentasikan prosedur dasar untuk kepatuhan awal.")
    return recs


def generate_checklist(analysis_list: List[Dict[str, Any]]) -> List[str]:
    """
    Buat checklist mitigasi dari kumpulan analisis.
    """
    checklist = []
    for analysis in analysis_list:
        clause = analysis.get("clause")
        verdict = analysis.get("verdict")
        if verdict != "Complied":
            checklist.append(f"Tinjau dan perbaiki klausul {clause}: verdict = {verdict}")
    if not checklist:
        checklist.append("Semua klausul telah terpenuhi. Tidak ada tindakan tambahan yang diperlukan.")
    return checklist


def compile_report(analysis_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Buat laporan lengkap dari hasil analisis.

    Returns struktur dict berisi:
    - gap_analysis: list analisis
    - recommendations: list rekomendasi global
    - checklist: list checklist mitigasi
    """
    # Gabungkan rekomendasi dari tiap klausul
    all_recs = []
    for a in analysis_list:
        all_recs.extend(generate_recommendations(a))
    # Hapus duplikat
    recommendations = list(dict.fromkeys(all_recs))
    checklist = generate_checklist(analysis_list)
    return {
        "gap_analysis": analysis_list,
        "recommendations": recommendations,
        "checklist": checklist
    }
