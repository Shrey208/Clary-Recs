import shutil
import joblib
import random
import sqlite3
import requests
import pandas as pd
from PIL import Image
import streamlit as st
from scipy.spatial import distance

st.set_page_config(
     page_title="Clary Recs",
     page_icon="Images/favicon.ico",
     layout="wide",
     initial_sidebar_state="expanded",
 )

menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        tbody th {display:none}
        .blank {display:none}
        </style>
        """
st.markdown(menu_style, unsafe_allow_html=True)

conn=sqlite3.connect("users.db")
c=conn.cursor()
@st.cache(allow_output_mutation=True, show_spinner=False)

def create_tables():
    c.execute("CREATE TABLE IF NOT EXISTS usertable(username TEXT, password TEXT);")
    c.execute("CREATE TABLE IF NOT EXISTS userdata(username TEXT, aname TEXT);")
    c.execute("CREATE TABLE IF NOT EXISTS superuser(username TEXT, password TEXT);")
def add_user(username, password):
    c.execute("INSERT INTO usertable(username,password) VALUES(?,?)",(username,password))
    conn.commit()
def check_user(username):
    c.execute("SELECT * FROM usertable WHERE username=?;",(username,))
    data = c.fetchall()
    return data
def view_users():
    c.execute("SELECT username FROM usertable")
    data = c.fetchall()
    return data
def login_user(username, password):
    c.execute("SELECT * FROM usertable WHERE username=? AND password=?;",(username,password))
    data = c.fetchall()
    return data 
def drop_user(username, password):
    c.execute("DELETE FROM usertable WHERE username=? AND password=?;",(username,password))
    conn.commit()
def add_anime(username, aname):
    c.execute("INSERT INTO userdata(username,aname) VALUES(?,?)",(username, aname))
    conn.commit()
def check_anime(username, aname):
    c.execute("SELECT * FROM userdata WHERE username=? AND aname=?;",(username, aname))
    data = c.fetchall()
    return data
def get_anime(username):
    c.execute("SELECT aname FROM userdata WHERE username=?;",(username,))
    data = c.fetchall()
    return data
def drop_anime(username):
    c.execute("DELETE FROM userdata WHERE username =?;",(username,))
    conn.commit()
def remove_anime(ussername, aname) :
    c.execute("DELETE FROM userdata WHERE username =? and aname =?;",(username,aname))
    conn.commit()
def login_su(username, password):
    c.execute("SELECT * FROM superuser WHERE username=? AND password=?;",(username,password))
    data = c.fetchall()
    return data
def su_pass(username):
    c.execute("SELECT password FROM usertable WHERE username=?;",(username,))
    data = c.fetchall()
    return data
def su_drop(username):
    c.execute("DELETE FROM usertable WHERE username=?;",(username,))
    conn.commit()
def aimg(aname):
    query = "https://unofficial-anilist-parser.herokuapp.com/anime/" + aname
    data = requests.get(query).json()
    res = requests.get(data['cover'], stream = True)
    if res.status_code == 200:
        with open("pic.jpg",'wb') as f:
            shutil.copyfileobj(res.raw, f)
    return data['URL']
def mimg(aname):
    query = "https://unofficial-anilist-parser.herokuapp.com/manga/" + aname
    data = requests.get(query).json()
    res = requests.get(data['cover'], stream = True)
    if res.status_code == 200:
        with open("pic.jpg",'wb') as f:
            shutil.copyfileobj(res.raw, f)
    return data['URL']
def recm(df, name, num):
    df2 = df.copy()
    uid = df[df['name']==name].index[0]
    dist = pd.DataFrame(data = df1.index)
    dist = dist[df1.index != uid]
    dist['distance'] = dist['anime_id'].apply(lambda x: distance.euclidean(df1.loc[x],df1.loc[uid]))
    dist.sort_values(by='distance' , inplace= True)
    rec = dist.head(num)
    df2 = pd.merge(df2, rec, on = "anime_id")
    df2.sort_values(by='distance' , inplace= True)
    df2.reset_index(drop=True, inplace=True)
    df2 = df2.drop(["anime_id", "type", "distance"], axis = 1)
    df2.sort_values(by='members' , inplace= True, ascending= False)
    df2.columns = map(str.capitalize, df2.columns)
    return df2

df = pd.read_csv('anime.csv')
df = df.dropna(how='any', axis=0)
topdf = df.drop(['anime_id', 'type'], axis = 1)
topdf = topdf.sort_values(by = ['members'], ascending=False).head(10)
topdf.columns = map(str.capitalize, topdf.columns)
df1 = df.drop(['name','episodes','members'], axis = 1)
gen = df1['genre'].str.get_dummies(sep=',')
typ =  pd.get_dummies(df1[['type']])
df1 = df1.drop(['genre', 'type'], axis =1)
df1 = pd.concat([df1,gen, typ], axis=1)
df1['rating'] = df1['rating']/10
df1.columns = df1.columns.str.lstrip()
df1 = pd.concat([df1[col].sum(axis=1).rename(col) if len(df1[col].shape)==2 else df1[col] for col in df1.columns.unique()],axis=1)
df = df.set_index('anime_id')
df1 = df1.set_index('anime_id')

st.title("Clary Recommends")
menu=["Home","Sign In","Sign Up", "Remove User","SuperUser Access", "About"]
choice=st.sidebar.selectbox("Menu",menu)
if choice =="Home":
    image = Image.open('Images/TitleImage.jpg')
    st.image(image, use_column_width=True)
    st.subheader("Top 10 Animes")
    st.table(topdf.style.format({"Rating": "{:.2f}"}))
elif choice=="Sign In":
    image = Image.open('Images/title.png')
    st.image(image, use_column_width=True)
    st.subheader("Sign In Section")
    if view_users():
        username=st.sidebar.text_input("User Name")
        password=st.sidebar.text_input("Password",type="password")
        if st.sidebar.checkbox("Sign In/Out"):
            create_tables()
            result = login_user(username,password)
            if result:
                st.success("Signed in as {}".format(username))
                task = st.radio("Please Select a Task", ["Recommend From Anime Collection", "Add Anime to My Collection", "Recommend From Last Watched", "Surprise Me!! From my Collection", "View Otaku Collections", "Remove Anime From My Collection"])
                if st.checkbox("Select Task"):
                    if task == "Recommend From Anime Collection":
                        option = st.selectbox('Select anime for recommendation', (df['name']))
                        if st.button("Get Recommendation"):
                            try:
                                url = aimg(option)
                                pic = Image.open('pic.jpg')
                                st.image(pic)
                                st.info("Details About " + option + " " + "[Here](%s)" % url)
                            except:
                                try:
                                    url = mimg(option)    
                                    pic = Image.open('pic.jpg')
                                    st.image(pic)
                                    st.info("Details About " + option + " " + "[Here](%s)" % url)
                                except:
                                    pass                       
                            finally:
                                st.warning("Finding Animes Like " + option)
                            res = recm(df, option, 20)
                            st.table(res.style.format({"Rating": "{:.2f}"}))
                            st.success("Now Go watch from above animes!!!!")
                    elif task == "Add Anime to My Collection":
                        option = st.selectbox('Select anime for adding', (df['name']))
                        if st.button("Add Anime"):
                            if check_anime(username, option):
                                st.warning(option + " already in your Collection")
                            else:
                                add_anime(username, option)
                                st.success(option +" added to your Collection")
                    elif task == "Recommend From Last Watched":
                        hist = get_anime(username)
                        if hist:
                            lw = hist[len(hist)-1][0]
                            st.success(lw + " was your last watched anime")
                            st.info("Finding Animes Like " + lw)
                            res = recm(df, lw, 20)
                            st.table(res.style.format({"Rating": "{:.2f}"}))
                            st.success("Now Go watch from above animes!!!!")
                        else:
                            st.warning("Your Collection is empty, our app is feeling unloved")
                    elif task == "Surprise Me!! From my Collection":
                        hist = get_anime(username)
                        if hist:
                            la = []
                            for i in hist:
                                la.append(i[0])
                            ran = random.choice(la)
                            st.success(ran + " Selected")
                            st.info("Finding Animes Like " + ran)
                            res = recm(df, ran, 20)
                            st.table(res.style.format({"Rating": "{:.2f}"}))
                            st.success("Now Go watch from above animes!!!!")
                        else:
                            st.warning("Your Collection is empty, our app is feeling unloved")
                    elif task == "View Otaku Collections":
                        vu = view_users()
                        vl = []
                        for i in vu:
                            vl.append(i[0])
                        rmu = st.selectbox('Select an Otaku', vl)
                        if st.button("Select Otaku"):
                            hist = get_anime(rmu)
                            if hist:
                                nme= ""
                                for i in hist:
                                    nme = nme + i[0] + "  \n"
                                st.info(nme)
                            elif username == rmu:
                                st.warning("Your Collection is empty, our app is feeling unloved")
                            else:
                                st.warning(rmu +"'s Collection is empty, maybe they don't love our app")
                    elif task == "Remove Anime From My Collection":
                        hist = get_anime(username)
                        if hist:
                            ral = []
                            for i in hist:
                                ral.append(i[0])
                            atm = st.selectbox('Select anime to remove', ral)
                            if st.button("Remove Anime"):
                                remove_anime(username, atm)
                                st.success(atm +" removed from your Collection")
                                st.checkbox("Check this box to Refresh Your Collection")
                        else:
                            st.warning("Your Collection is empty, our app is feeling unloved")
            else:
                st.warning("Incorrect Username/Password")
    else:
        st.warning("No Users Found, our app is feeling unloved")
elif choice=="Sign Up":
    image = Image.open('Images/SignUp.jpg')
    st.image(image, use_column_width=True)
    st.subheader("Sign Up Section")
    new_user=st.text_input("Username")
    new_password=st.text_input("Password",type="password")
    if st.button("Sign Up"):
        create_tables()
        result = check_user(new_user)
        if result:
            st.warning("Username already exsists")
        else :
            add_user(new_user,new_password)
            st.success("You have created an Otaku Account")
elif choice == "SuperUser Access":
    image = Image.open('Images/view.jpg')
    st.image(image, use_column_width=True)
    st.subheader("SuperUser Section")
    username=st.sidebar.text_input("User Name")
    password=st.sidebar.text_input("Password",type="password")
    if st.sidebar.checkbox("Sign In/Out"):
        result = login_su(username, password)
        if result:
            st.sidebar.success("SuperUser In")
            vu = view_users()
            if vu:
                vl = []
                for i in vu:
                    vl.append(i[0])
                rmu = st.selectbox('Select user to remove', vl)
                if st.checkbox("Reveal Password"):
                    st.success("Password for "+ rmu + " : " + su_pass(rmu)[0][0])
                if st.button("Remove User"):
                    su_drop(rmu)
                    drop_anime(rmu)
                    st.info("SuperUser removed user " + rmu)
                    st.checkbox("Check this box to Refresh the Database")
            else:
                st.warning("No Users Found, our app is feeling unloved")
        else:
            st.warning("Incorrect Username/Password")
elif choice == "Remove User":
    image = Image.open('Images/Title.jpg')
    st.image(image, use_column_width=True)
    st.subheader("Remove User Section")
    if view_users():
        username=st.text_input("User Name")
        password=st.text_input("Password",type="password")
        result=login_user(username,password)
        if st.button("Remove"):
            if result:
                drop_user(username,password)
                drop_anime(username)
                st.success("Rwemoved user {}".format(username))
            else :
                st.warning("Incorrect Username/Password")
    else:
        st.warning("No Users Found, our app is feeling unloved")
elif choice == "About" :
    st.subheader("About this App")
    st.success("A nice anime recommendation system to get your recommendations stored with your user profile. Simply SignUp and SignIn to the web-app, then select your favourite anime and click Get Recommendations. If you love the anime a little too much then you may add it to your Otaku collection as well.")
    st.subheader("Made By")
    st.info("[Shreyansh](https://shrey208.github.io/)")
    st.sidebar.markdown("[![Play Store](https://yourimageshare.com/ib/wAfw7ETFUn.png)](https://play.google.com/store/apps/details?id=com.prhgeyaw.ts_1648361227461)")