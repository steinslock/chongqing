# Goal 2.7 Face Detection Audit

Contact sheet directory: `/data4/qiangminc/code/chongqing/artifacts/goal2_7/face/contact_sheets`
Contact sheets found: `200`

| task | status | videos | blocked | mean_detection_rate | fallback_count | multi_face_rate |
| --- | --- | --- | --- | --- | --- | --- |
| self_intro | available | 3597 | 32 | 0.9903940369540873 | 3572 | 0.0234054217991788 |
| task | available | 3597 | 39 | 0.9831295806800432 | 3567 | 0.021713090899381903 |

Background masks remove the expanded face bounding box but may still preserve body, room, camera, and acquisition-context information; this remains a shortcut limitation.
