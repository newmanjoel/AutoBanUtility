import base64
import os
from urllib.parse import quote as urlquote
import time
from dash_bootstrap_components._components.Progress import Progress
import pyautogui
# install with 'pip install pyautogui'
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State, MATCH, ALL
from dash.exceptions import PreventUpdate
import ast
import pandas as pd
from datetime import datetime
import json


UPLOAD_DIRECTORY = "./data"
if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)


def static_vars(**kwargs):
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func
    return decorate


app = dash.Dash("HUH?", external_stylesheets=[dbc.themes.DARKLY])
container1 = dbc.Container(
    [
        dcc.Store(id='active-file-name', data=None),
        dcc.Store(id='active-file-path', data=None),
        dcc.Store(id='active-dataframe', data=None),
        dcc.Store(id='latest-file-id', data=None),
        dcc.Store(id='working-queue', data=None),
        dbc.Tabs(
            [
                dbc.Tab(label="Step 1. Choosing the file list", children=[
                    dbc.Collapse(children=[
                        html.H2("Upload"),
                        dcc.Upload(
                            id="upload-data",
                            children=html.Div(
                                ["Drag and drop or click to select a file to upload."]
                            ),
                            style={
                                "width": "100%",
                                "height": "60px",
                                "lineHeight": "60px",
                                "borderWidth": "1px",
                                "borderStyle": "dashed",
                                "borderRadius": "5px",
                                "textAlign": "center",
                                "margin": "10px",
                            },
                            multiple=True,
                        ),
                        html.H2("File List"),
                        html.Ul(id="file-list"),
                    ],
                        id="upload-collapse",
                        is_open=True,
                    ), ]),
                dbc.Tab(label="Step 2. Preview the usernames to delete", children=[
                    html.Div(
                        [
                            html.H2("Selected File"),
                            html.P(id="Selected-File"),
                            html.H2("Selected File Preview",
                                    id='Selected-File-Table-Label'),
                            html.Div(id='Selected-File-Table'),
                            #dbc.Input(id="input", placeholder="Type something...", type="text"),
                            html.Br(),
                            html.P(id="output"),

                        ]
                    ),
                ]),
            ]
        ),
        dcc.Interval(id="progress-interval", n_intervals=0, interval=500),
        html.H1("Ban People on twitch without having to log in!!"),
        dbc.Progress(id="progress-bar"),
        dbc.Button(
            "Start autoba(h)n-ing!",
            color="primary",
            block=True,
            id="start-typing",
            className="mb-3",
        ),
        html.Div(id='last-run-time'),
        # html.Div(
        #     [
        #         html.H2("Selected File"),
        #         html.P(id="Selected-File"),
        #         html.H2("Selected File Preview",
        #                 id='Selected-File-Table-Label'),
        #         html.Div(id='Selected-File-Table'),
        #         #dbc.Input(id="input", placeholder="Type something...", type="text"),
        #         html.Br(),
        #         html.P(id="output"),

        #     ]
        # ),
    ]
)

app.layout = container1


def save_file(name, content):
    """Decode and store a file uploaded with Plotly Dash."""
    data = content.encode("utf8").split(b";base64,")[1]
    with open(os.path.join(UPLOAD_DIRECTORY, name), "wb") as fp:
        fp.write(base64.decodebytes(data))


def uploaded_files():
    """List the files in the upload directory."""
    files = []
    for filename in os.listdir(UPLOAD_DIRECTORY):
        path = os.path.join(UPLOAD_DIRECTORY, filename)
        if os.path.isfile(path):
            files.append(filename)
    return files


def file_download_link(filename, index):
    """Create a Plotly Dash 'A' element that downloads a file from the app."""
    #location = "/download/{}".format(urlquote(filename))
    # return html.A(filename, href=location, id={'type':'file-list-item'})
    return dbc.Badge(filename, color="info", className="mr-1", id={'type': 'file-list-item', 'index': index}),


@app.callback(
    Output("file-list", "children"),
    [Input("upload-data", "filename"), Input("upload-data", "contents")],
    State('latest-file-id', 'data'),
)
def update_output(uploaded_filenames, uploaded_file_contents, uploaded_fileslatest_file_id):
    """Save uploaded files and regenerate the file list."""

    if uploaded_filenames is not None and uploaded_file_contents is not None:
        for name, data in zip(uploaded_filenames, uploaded_file_contents):
            save_file(name, data)

    files = uploaded_files()
    list_to_return = []
    if len(files) == 0:
        return [html.Li("No files yet!")]
    else:
        i = 0
        for filename in files:
            list_to_return.append(html.Li(file_download_link(filename, i)))
            i += 1
        return list_to_return


@app.callback(Output("Selected-File", "children"),
              Input("active-file-name", "data"))
def update_selected_file(active_file_name):
    if active_file_name is None:
        raise PreventUpdate
    return active_file_name


@app.callback(
    [Output('active-dataframe', 'data'), Output('working-queue', 'data')],
    Input('active-file-path', 'data'))
def load_selected_data(active_file_path):
    if active_file_path is None:
        raise PreventUpdate
    df = pd.read_csv(active_file_path, header=None, names=['username'])
    # print(df.head())
    returnString = df.to_json()
    return (returnString, returnString)


@app.callback(Output("upload-collapse", "is_open"), Input('active-dataframe', 'data'))
def hide_upload_section(active_dataframe):
    return active_dataframe is None


@app.callback(
    [
        Output('Selected-File-Table', 'children'),
        Output('Selected-File-Table-Label', 'children')
    ],
    Input('active-dataframe', 'data'))
def populate_table(active_dataframe):
    if active_dataframe is None:
        raise PreventUpdate
    df = pd.read_json(active_dataframe)
    return (dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True, size='sm'), f'Selected File Preview ({len(df)} items)')


@app.callback(Output("active-file-path", "data"), Input("active-file-name", "data"))
def get_active_file_path(active_file_name):
    if active_file_name is None:
        raise PreventUpdate
    return f'{UPLOAD_DIRECTORY}/{active_file_name}'


@app.callback(
    Output("active-file-name", "data"),
    Input({"type": "file-list-item", 'index': ALL}, 'n_clicks'),
    [
        State({"type": "file-list-item", 'index': ALL}, 'children'),
        State({"type": "file-list-item", 'index': ALL}, 'value')
    ])
def clicked_file(file_list_click, all_the_info, all_the_value):
    ctx = dash.callback_context

    if not ctx.triggered:
        raise PreventUpdate
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        button_id = ast.literal_eval(button_id)

    if all(v is None for v in file_list_click):
        raise PreventUpdate

    print(f'clicks-> {file_list_click}')
    print(f'info  -> {all_the_info}')
    print(f'button-> {button_id}')
    print(f'values-> {all_the_value}')

    return all_the_info[button_id["index"]]

# import csv
# bot_names = []
# # bot_list.csv is the file that contains all of the names to be banned
# # expects a format of one name per line with a space at the end
# with open('./data/bot_list_sep_28.csv', newline='' ) as csvfile:
#     spamreader = csv.reader(csvfile,delimiter=' ')
#     bot_names = [row[0].strip() for row in spamreader]

# print('Starting countdown')
# for i in range(10,0,-1):
#     #print(f"Writing text in {i} seconds")
#     #time.sleep(1)
#     pass


# n = len(bot_names)
# i = 0
# for userToBan in bot_names:
#     printingString = userToBan.ljust(50)
#     #print(f"\r({i*100/n}%) banning user {printingString}",end = '\r')
#     #pyautogui.write(f'/ban {userToBan}')
#     #pyautogui.press('enter')
#     #time.sleep(0.05)
#     i +=1

@app.callback(
    Output('last-run-time', 'children'),
    Input('start-typing', 'n_clicks'),
    State('active-dataframe', 'data'))
def auto_type_ban_usernames(start_n_clicks, active_dataframe):
    if active_dataframe is None:
        raise PreventUpdate

    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    df = pd.read_json(active_dataframe)
    n = len(df)
    i = 1

    print('Starting countdown')
    for i in range(10, 0, -1):
        print(f"Writing text in {i} seconds")
        time.sleep(1)
        pass

    for index, row in df.iterrows():
        print(f"({round(i/n*100,2)}%) banning user: {row['username']}")
        try:
            pyautogui.write(f"/ban {row['username']}")
            pyautogui.press('enter')
        except pyautogui.FailSafeException:
            return dbc.Toast(
                [html.P("Failsafe detected, Stopping the autotype", className="mb-0")],
                id="auto-toast",
                header="WOOOAH there autotyper",
                icon="primary",
                duration=10000,
            )
            return
        i += 1
        time.sleep(0.05)

    return datetime.now()
    # for userToBan in df.username:
    #     printingString = userToBan.ljust(50)
    #     #print(f"\r({i*100/n}%) banning user {printingString}",end = '\r')
    #     #pyautogui.write(f'/ban {userToBan}')
    #     #pyautogui.press('enter')
    #     #time.sleep(0.05)
    #     i +=1


if __name__ == "__main__":
    app.run_server(debug=True)
    pass


''' FORMAT OF THE DATASTORE DICTIONARY (active-dataframe)
{
    "username": {
        "0": "thetwitchauthority_e0244 ",
        "1": "vvmanolia ",
        "2": "no_id_uh ",
        "3": "thetwitchauthority2 ",
        "4": "phpshit ",
        "5": "night_php ",
        "6": "night_php_lunasec ",
        "7": "clickonmeplease6 ",
        "8": "maujior ",
        "9": "molsonfl ",
        "10": "0x45e ",
        "11": "ox45e ",
        "12": "0x25e ",
        "13": "0x45e_tta ",
        "14": "0x45e_banned "
    }
}
'''
