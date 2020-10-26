from features.create_features import get_time_hist, get_number_of_urls_published_before_source
import pandas as pd


def get_indecies(l):
    ids = []
    for i, x in enumerate(l):
        if x != 0:
            ids.append(i)
    return ids

def test_get_number_of_urls_published_before_source():
    dates_to_url = {
        "main_url": pd.to_datetime("2020-08-10 09:00:00"),
        "1_day_before": pd.to_datetime("2020-08-09 00:00:00"),
        "1_day_after": pd.to_datetime("2020-08-11 00:00:05"),
        "5_hours_before": pd.to_datetime("2020-08-10 05:00:00"),
        "None": None
    }
    main_url = "main_url"

    expected_number = 2
    actual_number = get_number_of_urls_published_before_source(dates_to_url, main_url)
    assert expected_number==actual_number

def test_get_time_hist():
    dates_to_url = {
        "main_url": pd.to_datetime("2020-08-10 00:00:00"),
        "5_second_later_url": pd.to_datetime("2020-08-10 00:00:05"),  # index 1
        "5_second_later_url_2": pd.to_datetime("2020-08-10 00:00:05"),  # index 1
        "1_hour_later_url": pd.to_datetime("2020-08-10 01:00:00"),  # 60
        "1_day_3_hours_34_seconds_later": pd.to_datetime("2020-08-11 03:00:32"),  # 24*60 +3*60+0=1620
        "3_days_later": pd.to_datetime("2020-08-13 00:00:00"),  # index 24 in hour
        "5_days_5h_6_minutes_later": pd.to_datetime("2020-08-15 05:06:47"),  # index 77
        "13_days_later": pd.to_datetime("2020-08-23 23:44:55"),  # index 6
        "36_dayes_later": pd.to_datetime("2020-09-26 12:34:55"),
    }
    url_to_level = {
        "main_url": -1,
        "5_second_later_url": 0,
        "5_second_later_url_2": 1,
        "1_hour_later_url": 0,
        "1_day_3_hours_34_seconds_later": 0,
        "3_days_later": 0,
        "5_days_5h_6_minutes_later": 0,
        "13_days_later": 0,
        "36_dayes_later": 1,
    }

    max_level = 2
    expected_dict = {
        "minute_hist": [0] * 24 * 60 * 2 * max_level,
        "hour_hist": [0] * 24 * 5 * max_level,
        "day_hist": [0] * 23 * max_level,
        "more_than_30_days": [0, 0],
    }
    expected_dict["minute_hist"][0] = 1
    expected_dict["minute_hist"][2880] = 1  # 2 index
    expected_dict["minute_hist"][60] = 1
    expected_dict["minute_hist"][1620] = 1
    expected_dict["hour_hist"][24] = 1
    expected_dict["hour_hist"][77] = 1
    expected_dict["day_hist"][6] = 1
    expected_dict["more_than_30_days"][1] = 1
    main_url = "main_url"
    actual_dict = get_time_hist(dates_to_url, url_to_level, main_url, max_level)

    # print(get_indecies(expected_dict["hour_hist"]),get_indecies(actual_dict["hour_hist"]))
    assert expected_dict["day_hist"] == actual_dict["day_hist"]
    assert expected_dict["minute_hist"] == actual_dict["minute_hist"]
    assert expected_dict["hour_hist"] == actual_dict["hour_hist"]
    assert expected_dict["more_than_30_days"] == actual_dict["more_than_30_days"]
