#!C:\Python27\python.exe
import cgi, cgitb, glob, os, sqlite3, Cookie, datetime, re, smtplib
from email.mime.text import MIMEText

def send_email(email, message, subject):
    #send a confirmation email to the new user
    #print 'Content-Type: text/plain\n\n'
    to_address = email
    from_address = 'andrewt@cse.unsw.edu.au'
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = from_address
    msg['To'] = to_address
    s = smtplib.SMTP('smtp.unsw.edu.au')
    s.sendmail(from_address, [to_address], msg.as_string())
    s.quit()
    #send a confirmation email to the new user

def main():
    global username
    global parameters
    global cookie
    global flag_listenTo_successfully
    global flag_unlistenTo_successfully

    string_cookie = os.environ.get('HTTP_COOKIE')
    cookie.load(string_cookie)
    own_username = cookie['sid'].value
    # logout handle
    if parameters.getvalue('action') == 'logout':
        global flag_logout
        flag_logout = 1

        #delete related session here
        cookie['sid'] = ''
        cookie['sid']['expires'] = 'Thu, 01 Jan 1970 00:00:00 GMT'
        print cookie

        prompt_logout = "logout successfully."
        redirect('./bitter.cgi')
    else:
        prompt_logout = ""
    # logout handle

    # listenTo handle
    conn = sqlite3.connect('users.db')
    if parameters.getvalue('listenTo') == "Listen":
        conn.execute("INSERT INTO LISTEN (USERNAME, FRIEND) VALUES (?, ?);", (own_username, username))
        flag_listenTo_successfully = 1
        conn.commit()
        cursor = conn.execute("SELECT email from user where username=?", (username,))
        for row in cursor:
            email = row[0]
        message = """
            Hi, the user %s listened you in bleat just now :)
        """ % own_username
        subject = "Bleat listen notification from Bitter"
        send_email(email, message, subject)
        cursor.close()

    elif parameters.getvalue('listenTo') == "Unlisten":
        conn.execute("DELETE FROM LISTEN WHERE USERNAME=? AND FRIEND=?;", (own_username, username))
        flag_unlistenTo_successfully = 1
        conn.commit()
        cursor = conn.execute("SELECT email from user where username=?", (username,))
        for row in cursor:
            email = row[0]
        message = """
            Hi, the user %s unlistened you in bleat just now :)
        """ % own_username
        subject = "Bleat unlisten notification from Bitter"
        send_email(email, message, subject)
        cursor.close()

    conn.close()
    # listenTo handle

    page = parameters.getvalue("page", 0)
    if page < 0:
        page = 0

    print page_header()  #header actually should be processd, it contain home, about, register, and username sign in with password
    dataset_size = "small"
    users_dir = "dataset-%s/users"% dataset_size
    print self_page(prompt_logout, parameters, users_dir)

    #print self_bleat()  # should be changed

    print bleats_page(page)

    print page_trailer(parameters)

def redirect(url):
    return "Location: %s" % url

def get_avatar(username):
    avatar = ""
    conn = sqlite3.connect('users.db')
    cursor = conn.execute("SELECT profile from user where username=?;", (username ,))
    for row in cursor:
        avatar = row[0]
    if avatar:
        url_avatar = "<img src=\"%s\" alt=\"Bitter\" class=\"img-circle\" height=\"50px\" width=\"50px\">" % avatar
    else:
        url_avatar = "<img src=\"avatar/default.jpg\" alt=\"Bitter\" class=\"img-circle\" height=\"50px\" width=\"50px\">"
    conn.close()
    return url_avatar

def create_topic_link(content):
    p = re.compile(r'#([\S]+)')
    at_result = p.findall(content)  # list : ['DaisyFuentes', 'DaisyFuentes']   at_result is a list contains only one bleat
    for at_value in at_result:
        oldstr = '#' + at_value
        newstr = "<a href=\"search.cgi?user_or_bleat=%23" + at_value + "\"><b>#" + at_value + "</b></a>"
        content = content.replace(oldstr, newstr, 1)
    return content

def bleats_page(page):
    global cookie
    global flag_login_successfully
    global username
    self_username = ""
    string_cookie = os.environ.get('HTTP_COOKIE')
    if string_cookie:
        cookie.load(string_cookie)
        if 'sid' in cookie:
            self_username = cookie['sid'].value

    conn = sqlite3.connect('users.db')
    cursor = conn.execute("SELECT count(*) from bleat where username=?", (username,))
    rows = cursor.fetchone()[0]
    number_of_page = rows // 12
    if rows % 12 == 0 and rows != 0:
        number_of_page -= 1
    ##### control the beginning number of pages #####
    offset = int(page) * 12
    limit = 12
    html = ""
    if (self_username != "" or flag_login_successfully == 1) and flag_logout == 0: #has already login
        cursor = conn.execute("SELECT username, content, time, in_reply_to, id from bleat where username =? order by time DESC limit ? offset ?;",(username, limit, offset))

    if cursor:
        html = "<div class=\"container\">"
    block = 0
    date_time = ""
    for row in cursor:
        if block % 2 == 0:
            html += "<div class=\"row\">"
        timestamp = row[2]
        date_time = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        content = row[1]
        reply_to = row[3]
        id = row[4]

        # create internal link for both other users and me who are being @, for other users, create a link, for myself, just bold it
        p = re.compile(r'@([\S]+)')
        at_result = p.findall(content)  # list : ['DaisyFuentes', 'DaisyFuentes']   at_result is a list contains only one bleat
        for at_value in at_result:
            if at_value == username:   # the value behind @ is a myself
                # create internal link for @user
                oldstr = '@' + at_value
                newstr = "@<b> %s </b>" % at_value
                content = content.replace(oldstr, newstr, 1)
                # create internal link for @user
            else:
                cursor2 = conn.execute("SELECT username from user where username=?", (at_value,))
                if cursor2:  # the value behind @ must be someone else
                    # create internal link for @user
                    oldstr = '@' + at_value
                    newstr = "@<a href=\"user.cgi?username=%s\"><b> %s </b></a>" % (at_value, at_value)
                    content = content.replace(oldstr, newstr, 1)
                    # create internal link for @user
                cursor2.close()
        content = create_topic_link(content)
        # create internal link for both other users and me who are being @, for other users, create a link, for myself, just bold it

        if (self_username != "" or flag_login_successfully == 1) and flag_logout == 0:
            user_link = "%s %s" % (get_avatar(username), username)

        post_or_participate = ""
        if reply_to:
            post_or_participate = "<b>posted</b>"
        else:
            post_or_participate = "<b>participated</b>"

        html += "<div class=\"col-md-6\">\
                    <h2> %s </h2><p><small>%s at %s</small></p>\
                    <p>%s</p>\
                    <p><a class=\"btn btn-default\" href=\"./detail.cgi?bleatID=%s\" role=\"button\">View details &raquo;</a></p>\
                </div>" % (user_link, post_or_participate, date_time, content, id)
        if block % 2 == 1:
            html += "</div>"
        block += 1
    if block % 2 == 1:
        html += "</div>"
    html += "</div>"

    html += """
    <hr>
    <div class="row">
        <div class="col-md-4 col-md-offset-1">
              <a id="previous" class="btn btn-success" href="?username=%s&&page=%d" role="button">&laquo;Prev Page</a>
        </div>
        <div class="col-md-2"><b style="font-size:large;">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
              Page %d </b>
        </div>
        <div class="col-md-4">
              <a id="next" class="btn btn-success pull-right" href="?username=%s&&page=%d" role="button">Next Page &raquo;</a>
        </div>
    </div>
    <br><br>
    <script type="text/javascript">
        $(function(){
            if( %d <= 0){
                 $("a#previous").click(function(event) {
                   return false;
                 });
            }
            if( %d >= %d){
                 $("a#next").click(function(event) {
                   return false;
                 });
            }
        })
    </script>
    """ % (username, int(page) - 1, int(page), username, int(page) + 1, int(page), int(page), number_of_page)

    conn.close()
    return html


def self_page(prompt_logout, parameters, users_dir):
    global username
    global cookie
    global home_latitude_map
    global home_longitude_map
    global flag_listenTo_successfully
    global flag_unlistenTo_successfully

    conn = sqlite3.connect('users.db')
    cursor = conn.execute("SELECT username, full_name, home_suburb, home_latitude, home_longitude, profile from USER where username=?", (username,))

    attr = ["username", "full_name", "home_suburb", "home_latitude", "home_longitude"]
    index = 0
    detail_user = ""
    imageUrl = ""
    for row in cursor:
    #username password email full_name home_suburb home_latitude home_longitude profile
        detail_user = ""
        index = 0
        for item in row:
            if index == 5:
                if item:
                    imageUrl = "./" + str(item)
                else:
                    imageUrl = "./avatar/default.jpg"
                break
            if item:
                if index == 3:
                    home_latitude_map = float(item)
                if index == 4:
                    home_longitude_map = float(item)
                detail_user += attr[index] + " : " + str(item) + "<br>"
                index += 1
            else:
                index += 1
        detail_user.rstrip("<br>")
    conn.close()

    # process listenTo operation
    prompt_listenTo_button = "Listen"
    string_cookie = os.environ.get('HTTP_COOKIE')
    cookie.load(string_cookie)
    own_username = cookie['sid'].value
    conn = sqlite3.connect('users.db')
    cursor = conn.execute("SELECT FRIEND from LISTEN where username=?", (own_username,))
    for row in cursor:
        if row[0] == username:
            prompt_listenTo_button = "Unlisten"
            break

     # process listenTo operation

    prompt_listenTo = ""
    if flag_listenTo_successfully == 1:
        prompt_listenTo = "Listen to successfully!"
    prompt_unlistenTo = ""
    if flag_unlistenTo_successfully == 1:
        prompt_unlistenTo = "Unlisten to successfully!"
    conn.close()
    return """
    <div class="jumbotron">
        <div class="container">
            <div class="col-md-4"><img src="%s" /></div>

            <div class="col-md-4">
                %s
                <br><br><form method="POST" action="">
                    <input type="hidden" name="listenTo" value=%s>
                    <button type="submit" class="btn btn-primary"> %s &raquo;</button>
                </form>
                <h4 style="color:blue;font-weight:bold;">%s</h4>
                <h4 style="color:red;font-weight:bold;">%s</h4>
            </div>

            <div class="col-md-4" id="mapholder"></div>
        </div>
    </div>
    """ % (imageUrl, detail_user, prompt_listenTo_button, prompt_listenTo_button, prompt_listenTo, prompt_unlistenTo)


#
# HTML placed at the top of every page
#
def page_header():
    return """Content-Type: text/html

    <!DOCTYPE html>
    <html lang="en">
    <head>
    <title>Bitter</title>
    <script src="./javascripts/jquery-2.1.4.min.js"></script>
    <script src="./javascripts/bootstrap.min.js"></script>
    <link rel='stylesheet' href='./stylesheets/bitter.css' />
    <link rel='stylesheet' href='./stylesheets/bootstrap.min.css' />
    <link rel='stylesheet' href='./stylesheets/bootstrap-responsive.min.css' />
    </head>
    <body>


    <nav class="navbar navbar-inverse navbar-fixed-top">
      <div class="container">
        <div class="navbar-header">
          <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#navbar" aria-expanded="false" aria-controls="navbar">
            <span class="sr-only">Toggle navigation</span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
          </button>
          <a class="navbar-brand" href="#">Bitter</a>
        </div>
        <div id="navbar" class="navbar-collapse collapse">

            <ul class="nav navbar-nav navbar-left">
                <li><a href="./bitter.cgi">Home</a> </li>
                <li> <a href="./setting.cgi">Profile</a> </li>
                <li> <a href="./bleat.cgi">Bleats</a> </li>
                <li> <a href="./friend.cgi">Friends</a> </li>

                <li> <a href="./relate.cgi">@Related</a> </li>
                <li> <a href="./participate.cgi">Participated</a> </li>
                <li> <a href="./comment.cgi">My Commented Posts</a> </li>
            </ul>
            <form method="get" action="./search.cgi" class="navbar-form navbar-left" role="search">
                <div class="form-group">
                  <input type="text" name="user_or_bleat" class="form-control" placeholder="Search User Or Bleat">
                </div>
                <button type="submit" class="btn btn-default">Search</button>
            </form>
            <ul class="nav navbar-nav navbar-right">
                <li><a href="./bitter.cgi?action=logout">Logout</a></li>
               <li><a href="./views/about.html">About</a></li>
            </ul>
        </div><!--/.navbar-collapse -->
      </div>
    </nav>
    """


#
# HTML placed at the bottom of every page
# It includes all supplied parameter values as a HTML comment
# if global variable debug is set
#
def page_trailer(parameters):
    global home_latitude_map
    global home_longitude_map
    html = ""
    if home_latitude_map != 0.0 and home_longitude_map != 0.0:
        html = """
        <script>
        var x = document.getElementById("mapholder");

        function getLocation() {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(showPosition, showError);
            } else {
                x.innerHTML = "Geolocation is not supported by this browser.";
            }
        }

        function showPosition(position) {
            var latlon = %f + "," + %f;
            var img_url = "http://maps.googleapis.com/maps/api/staticmap?center="
            +latlon+"&zoom=13&size=300x250&sensor=false";
            document.getElementById("mapholder").innerHTML = "<img src='"+img_url+"'>";
        }

        function showError(error) {
            switch(error.code) {
                case error.PERMISSION_DENIED:
                    x.innerHTML = "User denied the request for Geolocation."
                    break;
                case error.POSITION_UNAVAILABLE:
                    x.innerHTML = "Location information is unavailable."
                    break;
                case error.TIMEOUT:
                    x.innerHTML = "The request to get user location timed out."
                    break;
                case error.UNKNOWN_ERROR:
                    x.innerHTML = "An unknown error occurred."
                    break;
            }
        }
        window.onload = getLocation;
        </script>
        """ % (home_latitude_map, home_longitude_map)
    else:
        html = """
        <script>
        var x = document.getElementById("mapholder");

        function getLocation() {
            x.innerHTML = "";
        }
        window.onload = getLocation;
        </script>
        """

    if debug:
        html += "".join("<!-- %s=%s -->\n" % (p, parameters.getvalue(p)) for p in parameters)
    html += "</body>\n</html>"
    return html

if __name__ == '__main__':
    cookie = Cookie.SimpleCookie()
    cgitb.enable()
    parameters = cgi.FieldStorage()      	#FieldStorage(None, None, [])  now
    username = parameters.getvalue('username')
    flag_logout = 0
    home_latitude_map = 0.0
    home_longitude_map = 0.0
    flag_listenTo_successfully = 0
    flag_unlistenTo_successfully = 0
    debug = 1

    # for debugging
    #para = ""
    # for debugging

    main()


