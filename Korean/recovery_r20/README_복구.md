# r20 번역 복구 결과 (2026-10-13)

## 파일
- gmd_ko_r20_recovered.csv : 앞으로 작업할 기준 번역 CSV. v13_2를 바탕으로 r20 패치에 들어간 번역을 다시 반영한 파일
- r20_vs_v13_2_changes.csv : v13_2 대비 r20에서 바뀐 15,970행 (r15~r20 교정 내역)
- r20_unmatched_entries.csv : CSV에 대응하는 행이 없는 GMD 항목 6건
- qa_issues.csv / qa_term_inconsistency.csv / qa_summary.json : 품질 점검 결과
- tools/ : 복호화(ddonarc.py), 복구(recover_r20.py), 역검증(verify_forward.py), 품질 점검(quality_scan.py)

## 검증
- r20 ARC 1,511개 복호화 → GMD 2,950개 매칭
- 복구한 CSV로 Arrowgene packGmd 매칭 규칙을 다시 적용 → r20 문자열과 82,107건 일치, 불일치 0건
- 복구에서 빠진 것: CSV에 행이 없는 6건, CSV에 없는 caplink UI ARC 6개(r20 바이너리에만 존재)

## 실행 (py -3.10, pycryptodome 필요)
py -3.10 tools\recover_r20.py <v13_2 CSV> <r20 payload\nativePC\rom> <출력폴더>
