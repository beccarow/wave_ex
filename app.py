import pandas as pd
import numpy as np

from h2o_wave import Q, app, main, ui, data

df = pd.read_csv('spotify_recs_2023_proc.csv')

@app('/')

async def server(q: Q):
    if not q.client.initialized:
        init_songs(q)
        apply_layout(q)
    q.client.initialized = True

    show_landing(q)
    show_plot(q, df)
    update_query_songs(q)
    if q.args.songs:  # Only proceed if songs are selected
        q.client.songs = q.args.songs
        display_recommendations(q)

    await q.page.save()

def show_landing(q:Q):
    q.page['header'] = ui.header_card(
        box=ui.box('header', width='100%', height='86px'),
        icon='MusicInCollectionFill',
        icon_color='Black',
        title='Spotify Top Song Recommendations',
        subtitle='Find similar songs on Spotify')


def apply_layout(q: Q):
    # Add flex layout if time allows
    q.page['meta'] = ui.meta_card(box='', theme='nord', layouts=[
        ui.layout(
            breakpoint='xl',
            width='1600px',
            zones=[
                ui.zone('header', size='80px'),
                ui.zone('body', direction=ui.ZoneDirection.ROW, zones=[
                    ui.zone('content', direction=ui.ZoneDirection.COLUMN, zones=[
                        ui.zone('section1'),
                        ui.zone('top', size='600px', direction = ui.ZoneDirection.ROW, zones=[
                            ui.zone('query', size='300px'),
                            ui.zone('recommendations'),
                        ]),
                        ui.zone('section2'),
                        ui.zone('bottom', direction=ui.ZoneDirection.ROW), 
                    ]),
                ]),
                ui.zone('footer')
            ]),
    ])

    q.page['recommendations'] = ui.form_card(box=ui.box('recommendations'), items=[]) #, width = '40%'

    q.page['query'] = ui.form_card(
            box=ui.box('query'), #, width = '49.5%'
            items=[
                ui.separator('Song Selection'),
                ui.text('Pick a song to receive recommendations'),
                ui.picker(
                    name='songs',
                    choices=[ui.choice(name=str(song), label=str(song)) for song in get_song_names(df)],
                    values=q.client.songs,
                    trigger=True,
                ),
                #ui.button(name='show_inputs', label='Get Recommendations', primary=True),    
            ]
        )

def init_songs(q:Q):
    q.client.songs = []
    q.client.liked_songs = []


def update_query_songs(q:Q):
    q.page['query'].items[2].picker.values = q.client.songs

def display_recommendations(q:Q):
    print(f"q.client.songs: {q.client.songs}")
    recs = get_recs(df, q.client.songs)
    print(f"Recommendations: {recs}")  # Debug print

    q.page['recommendations'].items = [
        ui.separator(label='You Might Also Like...'),
        *[
            ui.button(name='rec_btn', label=rec.strip('[]').replace("''",''), value=rec.strip('[]').replace("''",'')) for rec in recs
        ],
    ]

def get_song_names(df):
    return list(set(df.track_name.values))

def get_top_artists(df):
    top = df.groupby(['artist(s)_name']).sum()
    return top.sort_values('streams', ascending=False)[:10]

def make_artist_plot_data(df):
    top_10 = get_top_artists(df)
    return [(x, y) for x, y in zip(top_10.index.tolist(), top_10.streams.tolist())]




def show_plot(q:Q, df):
    q.page['plot'] = ui.form_card(
        box=ui.box('bottom'),
        items=[
            ui.text_xl('Most Popular Artists by Streams'),
            ui.visualization(
                plot=ui.plot([ui.mark(type='interval', x='=artist', y='=streams', y_min=0)]),
                data=data(
                    fields='artist streams',
                    rows=make_artist_plot_data(df),
                    pack=True),
            ),
        ],
    )
    

def get_recs(df, query_titles):
    recs = []
    for title in query_titles:
        rec_songs = df.loc[df['track_name'] == title]['recommendations'].to_list()[0]
        if isinstance(rec_songs, str):  # Check if rec_songs is a string
            rec_songs = rec_songs.split(",") # Split the string into a list
        recs.extend(rec_songs)
    return recs


