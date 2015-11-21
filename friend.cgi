#!C:\Python27\python.exe
import cgi, cgitb, glob, os, sqlite3, Cookie, datetime

def main():
    global username
    global parameters
    global cookie

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

    print page_header()  #header actually should be processd, it contain home, about, register, and username sign in with password
    dataset_size = "small"
    users_dir = "dataset-%s/users"% dataset_size
    print self_page(prompt_logout, parameters, users_dir)
    print page_trailer(parameters)

def redirect(url):
    return "Location: %s" % url

def self_page(prompt_logout, parameters, users_dir):
    global username
    global cookie
    string_cookie = os.environ.get('HTTP_COOKIE')
    cookie.load(string_cookie)
    own_username = cookie['sid'].value

    html = ""
    html += "<div class=\"jumbotron\"><div class=\"container\">"
    conn = sqlite3.connect('users.db')
    cursor = conn.execute("SELECT FRIEND from LISTEN where username=? order by friend", (own_username,))
    divide = 0
    for row in cursor:
        user_tmp = row[0]
        cursor2 = conn.execute("SELECT username, full_name, home_suburb, home_latitude, home_longitude, profile from USER where username=?", (row[0],))
        attr = ["username", "full_name", "home_suburb", "home_latitude", "home_longitude"]
        detail_user = ""
        index = 0
        imageUrl = ""
        for row in cursor2:
            detail_user = ""
            index = 0
            for item in row:
                if index == 5:
                    if item:
                        imageUrl = str(item)
                    else:
                        imageUrl = "avatar/default.jpg"
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

        jumbotron = ""
        new_row = ""
        new_row_finish = ""
        new_row = ""
        new_row_finish = ""
        jumbotron_finish = ""
        if divide % 2 == 0:
            #jumbotron = "<div class=\"jumbotron\"><div class=\"container\">"
            new_row = "<div class=\"row\">"
        else:
            new_row_finish = "</div><br>"
            #jumbotron_finish = "</div></div>"

        html += """
                %s
                <div class="col-md-3"><img src="%s" /></div>
                <div class="col-md-3">
                    %s
                    <br><br><p><a class="btn btn-primary" href=user.cgi?username=%s role="button">Home Page &raquo;</a></p>
                </div>
                %s
                """ % (new_row, imageUrl, detail_user, user_tmp, new_row_finish)
        divide += 1
    html += "</div></div>"
    conn.close()
    return html


#
# HTML placed at the top of every page
#
def page_header():
    return """Content-Type: text/html

    <!DOCTYPE html>
    <html lang="en">
    <head>
    <title>Bitter</title>
    <script src="javascripts/jquery-2.1.4.min.js"></script>
    <script src="javascripts/bootstrap.min.js"></script>
    <link rel='stylesheet' href='stylesheets/bitter.css' />
    <link rel='stylesheet' href='stylesheets/bootstrap.min.css' />
    <link rel='stylesheet' href='stylesheets/bootstrap-responsive.min.css' />
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
                <li><a href="bitter.cgi">Home</a> </li>
                <li> <a href="setting.cgi">Profile</a> </li>
                <li> <a href="bleat.cgi">Bleats</a> </li>
                <li> <a href="">Friends</a> </li>
                <li> <a href="relate.cgi">@Related</a> </li>
                <li> <a href="participate.cgi">Participated</a> </li>
                <li> <a href="comment.cgi">My Commented Posts</a> </li>
            </ul>
            <form method="get" action="../search.cgi" class="navbar-form navbar-left" role="search">
                <div class="form-group">
                  <input type="text" name="user_or_bleat" class="form-control" placeholder="Search User Or Bleat">
                </div>
                <button type="submit" class="btn btn-default">Search</button>
            </form>
            <ul class="nav navbar-nav navbar-right">
                <li><a href="bitter.cgi?action=logout">Logout</a></li>
               <li><a href="../views/about.html">About</a></li>
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
    html = ""
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
    debug = 1

    # for debugging
    #para = ""
    # for debugging
    main()


