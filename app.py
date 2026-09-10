from flask import Flask, render_template, request

from timetable_service import (
    load_trains,
    select_outbound_trains,
    select_return_trains,
    sort_outbound_trains_for_display,
    calculate_timeline_range,
    generate_time_ticks,
    build_train_lane,
    calculate_top,
    is_valid_search_time,
    build_train_diagram_points,
)


app = Flask(__name__)

OUTBOUND_STATIONS = [
    {
        "name": "茨木",
        "arrival_key": None,
        "departure_key": "茨木発",
    },
    {
        "name": "新大阪",
        "arrival_key": "新大阪着",
        "departure_key": "新大阪発",
    },
    {
        "name": "大阪",
        "arrival_key": "大阪着",
        "departure_key": "大阪発",
    },
    {
        "name": "尼崎",
        "arrival_key": "尼崎着",
        "departure_key": "尼崎発",
    },
    {
        "name": "西宮",
        "arrival_key": None,
        "departure_key": "西宮発",
    },
    {
        "name": "芦屋",
        "arrival_key": "芦屋着",
        "departure_key": "芦屋発",
    },
    {
        "name": "住吉",
        "arrival_key": None,
        "departure_key": "住吉発",
    },
    {
        "name": "六甲道",
        "arrival_key": None,
        "departure_key": "六甲道発",
    },
    {
        "name": "三ノ宮",
        "arrival_key": None,
        "departure_key": "三ノ宮発",
    },
    {
        "name": "元町",
        "arrival_key": None,
        "departure_key": "元町発",
    },
    {
        "name": "神戸",
        "arrival_key": None,
        "departure_key": "神戸発",
    },
]


@app.route("/", methods=["GET", "POST"])
def index():

    diagram_trains = []

    diagram_start_minutes = None
    diagram_end_minutes = None

    diagram_pixels_per_minute = 10
    diagram_top_margin = 50
    diagram_station_spacing = 90

    diagram_width = 0
    diagram_height = 0

    selected_trains = []
    train_lanes = []
    time_ticks = []

    direction = "outbound"
    target_time = ""

    start_minutes = None
    end_minutes = None
    target_top = None
    error_message = None

    timeline_height = 0

    pixels_per_minute = 14
    diagram_offset = 24

    # 検索ボタンが押されたときだけ処理する
    if request.method == "POST":
        direction = request.form["direction"]
        target_time = request.form["target_time"]

        # -------------------------
        # 行き
        # -------------------------
        if direction == "outbound":
            trains = load_trains("to-kobe.csv")

            # 検索可能時間か確認
            if not is_valid_search_time(
                direction="outbound",
                target_time=target_time,
                trains=trains,
            ):
                error_message = (
                    "行きの希望到着時刻は、"
                    "始発から9:30までを指定してください。"
                )

            else:
                selected_trains = select_outbound_trains(
                    trains,
                    target_time
                )

                # 神戸時刻の早い順に並べる
                selected_trains = sort_outbound_trains_for_display(
                    selected_trains
                )

                # 新しいダイヤグラム用の時間範囲
                diagram_start_minutes, diagram_end_minutes = calculate_timeline_range(
                    selected_trains
                )

                # 列車10本をSVG用の座標データに変換
                for train in selected_trains:
                    points = build_train_diagram_points(
                        train=train,
                        stations=OUTBOUND_STATIONS,
                        start_minutes=diagram_start_minutes,
                        pixels_per_minute=diagram_pixels_per_minute,
                        top_margin=diagram_top_margin,
                        station_spacing=diagram_station_spacing,
                    )

                    diagram_trains.append({
                        "train_type": train["train_type"],
                        "kobe_time": train["神戸発"],
                        "points": points,
                    })

                # SVG本体のおおよそのサイズ
                diagram_width = (
                        (diagram_end_minutes - diagram_start_minutes)
                        * diagram_pixels_per_minute
                )

                diagram_height = (
                        diagram_top_margin * 2
                        + (len(OUTBOUND_STATIONS) - 1)
                        * diagram_station_spacing
                )

                start_minutes, end_minutes = calculate_timeline_range(
                    selected_trains
                )

                target_top = calculate_top(
                    time_text=target_time,
                    start_minutes=start_minutes,
                    pixels_per_minute=pixels_per_minute,
                )

                timeline_height = (
                    (end_minutes - start_minutes)
                    * pixels_per_minute
                ) + (diagram_offset * 2)

                time_ticks = generate_time_ticks(
                    start_minutes,
                    end_minutes
                )

                for train in selected_trains:
                    lane = build_train_lane(
                        train=train,
                        stations=OUTBOUND_STATIONS,
                        start_minutes=start_minutes,
                        pixels_per_minute=pixels_per_minute,
                    )

                    first_top = lane[0]["top"] if lane else 0
                    last_top = lane[-1]["top"] if lane else 0

                    train_lanes.append({
                        "train_type": train["train_type"],
                        "stops": lane,
                        "line_top": first_top,
                        "line_height": last_top - first_top,
                    })

        # -------------------------
        # 帰り
        # -------------------------
        elif direction == "return":
            trains = load_trains("to-ibaraki.csv")

            # 検索可能時間か確認
            if not is_valid_search_time(
                direction="return",
                target_time=target_time,
                trains=trains,
            ):
                error_message = (
                    "帰りの希望出発時刻は、"
                    "15:00から終電までを指定してください。"
                )

            else:
                selected_trains = select_return_trains(
                    trains,
                    target_time
                )

    return render_template(
        "index.html",
        selected_trains=selected_trains,
        train_lanes=train_lanes,
        time_ticks=time_ticks,
        direction=direction,
        target_time=target_time,
        start_minutes=start_minutes,
        end_minutes=end_minutes,
        pixels_per_minute=pixels_per_minute,
        target_top=target_top,
        timeline_height=timeline_height,
        diagram_offset=diagram_offset,
        error_message=error_message,
        diagram_trains=diagram_trains,
        diagram_pixels_per_minute=diagram_pixels_per_minute,
        diagram_top_margin=diagram_top_margin,
        diagram_station_spacing=diagram_station_spacing,
        diagram_width=diagram_width,
        diagram_height=diagram_height,
        diagram_start_minutes=diagram_start_minutes,
        diagram_end_minutes=diagram_end_minutes,
        outbound_stations=OUTBOUND_STATIONS,
    )


if __name__ == "__main__":
    app.run(debug=True)