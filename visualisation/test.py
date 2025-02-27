from display_sankey import *
from display_gantt import *

import pandas as pd
import plotly.express as px
import datetime
import itertools
import os

result_directory_path = r"./"
result_file_name = "exemple_sortie.xlsx"
result_file_path = os.path.join(result_directory_path, result_file_name)

result_df = pd.read_excel(result_file_path, sheet_name=MACHINE_TASKS_SHEET)
dummy_date = datetime.date(2000, 1, 1)
tasks = []
resource_per_machine = {}
for task_id, task_type, task_pd_datetime, task_hour_datetime, task_duration, task_train in zip(
        result_df[ResultColumnNames.TASK_ID],
        result_df[ResultColumnNames.TASK_TYPE],
        result_df[ResultColumnNames.TASK_DATE],
        result_df[ResultColumnNames.TASK_HOUR],
        result_df[ResultColumnNames.TASK_DURATION],
        result_df[ResultColumnNames.TASK_TRAIN],
):
    task_date_datetime = task_pd_datetime.to_pydatetime()
    task_start = datetime.datetime.combine(dummy_date, task_hour_datetime)
    task_resource = get_resource_name(task_type, task_date_datetime.date())
    tasks.append(
        dict(
            Train=task_train,
            Start=task_start,
            Finish=task_start+datetime.timedelta(minutes=task_duration),
            Machine=task_type,
            Resource=task_resource
        )
    )
    resource_per_machine.setdefault(task_type, set()).add(
        get_resource_name(task_type, task_date_datetime.date()))
gantt_df = pd.DataFrame(tasks)
sorted_resources = list(itertools.chain.from_iterable(
    [sorted(resource_per_machine[machine]) for machine in ORDERED_MACHINES]
))

fig = px.timeline(gantt_df, x_start="Start", x_end="Finish",
                  y="Resource", color="Train")
fig.update_layout(xaxis=dict(title='Timestamp', tickformat='%H:%M:%S'))
fig.update_yaxes(categoryorder="array", categoryarray=sorted_resources[::-1])
fig.show()

input_directory_path = r"./"
# input_file_name = "instance_WPY_simple.xlsx"
input_file_name = "instance_WPY_realiste_jalon1.xlsx"
input_file_path = os.path.join(input_directory_path, input_file_name)

filter_on_departure_date = True
departure_date_filter = "13/08/2022"

input_df = pd.read_excel(
    input_file_path,
    sheet_name=CORRESPONDANCES_SHEET,
    converters={
        CorrespondanceColumnNames.WAGON_ID: str,
        CorrespondanceColumnNames.ARRIVAL_DATE: str,
        CorrespondanceColumnNames.ARRIVAL_TRAIN_NUMBER: str,
        CorrespondanceColumnNames.DEPARTURE_DATE: str,
        CorrespondanceColumnNames.DEPARTURE_TRAIN_NUMBER: str,
    }
)

if filter_on_departure_date:
    input_df = input_df[input_df[CorrespondanceColumnNames.DEPARTURE_DATE]
                        == departure_date_filter]

input_df[CorrespondanceColumnNames.ARRIVAL_TRAIN_ID] = (
    input_df[CorrespondanceColumnNames.ARRIVAL_TRAIN_NUMBER]
    + " "
    + input_df[CorrespondanceColumnNames.ARRIVAL_DATE]
)
arrival_train_ids = input_df[CorrespondanceColumnNames.ARRIVAL_TRAIN_ID].drop_duplicates(
).values.tolist()
arrival_train_idx_per_id = {
    train_id: train_idx
    for train_idx, train_id in enumerate(arrival_train_ids)
}
arrival_trains_amount = len(arrival_train_idx_per_id)

input_df[CorrespondanceColumnNames.DEPARTURE_TRAIN_ID] = (
    input_df[CorrespondanceColumnNames.DEPARTURE_TRAIN_NUMBER]
    + " "
    + input_df[CorrespondanceColumnNames.DEPARTURE_DATE]
)
departure_train_ids = input_df[CorrespondanceColumnNames.DEPARTURE_TRAIN_ID].drop_duplicates(
).values.tolist()
departure_train_idx_per_id = {
    train_id: train_idx
    for train_idx, train_id in enumerate(departure_train_ids)
}

link_sources = []
link_targets = []
link_values = []
idx_offset = arrival_trains_amount
link_idx = 0
link_idx_per_id = {}
for wagon_id, arrival_train_id, departure_train_id in zip(
    input_df[CorrespondanceColumnNames.WAGON_ID],
    input_df[CorrespondanceColumnNames.ARRIVAL_TRAIN_ID],
    input_df[CorrespondanceColumnNames.DEPARTURE_TRAIN_ID],
):
    link_id = get_link_id(arrival_train_id, departure_train_id)
    if link_id not in link_idx_per_id:
        link_sources.append(arrival_train_idx_per_id[arrival_train_id])
        link_targets.append(
            departure_train_idx_per_id[departure_train_id] + idx_offset)
        link_values.append(1)
        link_idx_per_id[link_id] = link_idx
        link_idx += 1
    else:
        link_values[link_idx_per_id[link_id]] += 1

fig = go.Figure(go.Sankey(
    arrangement='snap',
    node=dict(
        label=arrival_train_ids+departure_train_ids,
        pad=10,
        thickness=20,
    ),
    link=dict(
        arrowlen=15,
        source=link_sources,
        target=link_targets,
        value=link_values,
        hovertemplate='%{value} wagons<br />'
        'du sillon "%{source.label}"<br />'
        'au sillon "%{target.label}"<br /><extra></extra>',
    )
))
fig.show()
