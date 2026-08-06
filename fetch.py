from datetime import datetime, timezone, timedelta
import json
import os
import requests

# 車両番号のマッピング辞書
CAR_MAP = {
    "heichiku01": "412",
    "heichiku02": "409",
    "heichiku03": "401",
    "heichiku05": "403",
    "heichiku06": "501",
    "heichiku07": "410",
    "heichiku08": "406",
    "heichiku09": "411",
    "heichiku10": "408",
    "heichiku11": "407",
    "heichiku12": "404",
    "heichiku13": "405",
}

API_URL = "https://heichiku-imadoko.com/data/imadokoData.json"
SAVE_FILE = "train_history.json"


def fetch_and_process():
  # 1. データ取得
  response = requests.get(API_URL, timeout=10)
  response.raise_for_status()
  raw_data = response.json()

  # 2. 配列の末尾（下）から走査し、loginIdごとの最新データのみを抽出
  seen_logins = set()
  latest_items = []

  for item in reversed(raw_data):
    login_id = item.get("loginId")
    if login_id and login_id not in seen_logins:
      seen_logins.add(login_id)
      latest_items.append(item)

  # 日本時間の現在時刻を取得
  JST = timezone(timedelta(hours=9))
  fetched_at = datetime.now(JST).isoformat()

  # 3. データの整形・変換（360000で除算）
  processed_records = []
  for item in latest_items:
    login_id = item.get("loginId")
    car_no = CAR_MAP.get(login_id, login_id)

    # 緯度・経度を360000で除算（約33.7°N, 130.9°E 付近の値になります）
    lat = round(float(item["latitude"]) / 360000.0, 6)
    lng = round(float(item["longitude"]) / 360000.0, 6)

    record = {
        "fetchedAt": fetched_at,
        "carNo": car_no,
        "loginId": login_id,
        "lat": lat,
        "lng": lng,
        "gpsTime": item.get("gpsTime"),
        "terminalCd": item.get("terminalCd"),
    }
    processed_records.append(record)

  # 4. 既存ファイルに追記して保存
  history_data = []
  if os.path.exists(SAVE_FILE):
    try:
      with open(SAVE_FILE, "r", encoding="utf-8") as f:
        history_data = json.load(f)
    except json.JSONDecodeError:
      history_data = []

  history_data.extend(processed_records)

  with open(SAVE_FILE, "w", encoding="utf-8") as f:
    json.dump(history_data, f, ensure_ascii=False, indent=2)

  print(
      f"[{fetched_at}] {len(processed_records)}件の最新列車位置を追加保存しました。"
  )


if __name__ == "__main__":
  fetch_and_process()