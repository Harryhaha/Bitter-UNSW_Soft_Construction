#!C:\Python27\python.exe
import cgi, cgitb, glob, os, sqlite3, Cookie, datetime, re

def main():
    global user_or_bleat
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
    print search_page(prompt_logout, parameters, users_dir)

    #print self_bleat()  # should be changed

    #print bleats_page()

    print page_trailer(parameters)

def redirect(url):
    return "Location: %s" % url

def create_topic_link(content):
    p = re.compile(r'#([\S]+)')
    at_result = p.findall(content)  # list : ['DaisyFuentes', 'DaisyFuentes']   at_result is a list contains only one bleat
    for at_value in at_result:
        oldstr = '#' + at_value
        newstr = "<a href=\"search.cgi?user_or_bleat=%23" + at_value + "\"><b>#" + at_value + "</b></a>"
        content = content.replace(oldstr, newstr, 1)
    return content

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

def search_page(prompt_logout, parameters, users_dir):
    global user_or_bleat
    global cookie
    global flag_listenTo_successfully
    global flag_unlistenTo_successfully

    string_cookie = os.environ.get('HTTP_COOKIE')
    cookie.load(string_cookie)
    own_username = cookie['sid'].value

    user_or_bleat = '%' + user_or_bleat + '%'
    conn = sqlite3.connect('users.db')
    cursor = conn.execute("SELECT username, full_name from USER where (username like ? or full_name like ?) and username in (select friend from listen where username=?) order by username, full_name", (user_or_bleat, user_or_bleat, own_username))

    html = ""
    html += "<div class=\"container\">"
    html += "<div class=\"row\"><div class=\"col-md-6\">"
    html += "<h3>Result for user search:</h3><hr>"
    html += "<h4>Result from friends:</h4>"
    for row in cursor:
        username = row[0]
        url_avatar = get_avatar(username)
        full_name = row[1]
        html += """<div class="row">
                        <div class="col-sm-offset-1">
                            <a href=user.cgi?username=%s><h4>%s username: %s | full name: %s </h4></a>
                        </div>
                   </div><br>""" % (username, url_avatar, username, full_name)
    html += "<hr>"

    cursor.close()
    #conn = sqlite3.connect('users.db')
    cursor = conn.execute("SELECT username, full_name from USER where ( username like ? or full_name like ? ) and username not in (select friend from listen where username=?) and username!=? order by username, full_name", (user_or_bleat, user_or_bleat, own_username, own_username))
    html += "<h4>Result from others:</h4>"
    for row in cursor:
        username = row[0]
        url_avatar = get_avatar(username)
        full_name = row[1]
        html += """<div class="row">
                        <div class="col-sm-offset-1">
                            <a href=user.cgi?username=%s><h4>%s username: %s / full_name: %s </h4></a>
                        </div>
                    </div><br>""" % (username, url_avatar, username, full_name)

    html += "</div>"
    cursor.close()
    html += "<div class=\"col-md-6\">"
    html += "<h3>result for bleat search:</h3><hr>"

    # bleat search for myself
    html += "<h4>Result from myself:</h4>"

    cursor = conn.execute("SELECT username, content, time, in_reply_to, id from BLEAT where content like ? and username=? order by time DESC", (user_or_bleat, own_username))
    for row in cursor:
        username = row[0]
        url_avatar = get_avatar(username)
        timestamp = row[2]
        date_time = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        content = row[1]
        id = row[4] #for view details

        # create internal link for both other users and me who are being @, for other users, create a link, for myself, just bold it
        p1 = re.compile(r'@([\S]+)')
        at_result = p1.findall(content)  # list : ['DaisyFuentes', 'DaisyFuentes']   at_result is a list contains only one bleat
        for at_value in at_result:
            if at_value == own_username:   # the value behind @ is a myself
                # create internal link for @user
                oldstr = '@' + at_value
                newstr = "@<b> %s </b>" % at_value
                content = content.replace(oldstr, newstr, 1)
                # create internal link for @user
            else:
                cursor = conn.execute("SELECT username from user where username=?", (at_value,))
                if cursor:  # the value behind @ must be someone else
                    # create internal link for @user
                    oldstr = '@' + at_value
                    newstr = "@<a href=\"user.cgi?username=%s\"><b> %s </b></a>" % (at_value, at_value)
                    content = content.replace(oldstr, newstr, 1)
                    # create internal link for @user
                cursor.close()
        content = create_topic_link(content)
        # create internal link for both other users and me who are being @, for other users, create a link, for myself, just bold it

        reply_to = row[3]
        post_or_participate = ""
        if not reply_to:
            post_or_participate = "posted"
        else:
            post_or_participate = "participated"

        html += """
             <div class="row">
                <div class="col-sm-offset-1">
                     <h4>%s <b> %s </b></h4>
                     <p><small><b> %s </b> at %s</small></p>
                     <p>%s</p>
                     <p><a class="btn btn-default" href="detail.cgi?bleatID=%s" role="button">View details &raquo;</a></p>
                </div>
             </div><br>
             """ % (url_avatar, username, post_or_participate, date_time, content, id)
    html += "<hr>"
    if cursor:
        cursor.close()
    # bleat search for myself

    html += "<h4>Result from friends:</h4>"
    cursor = conn.execute("SELECT username, content, time, in_reply_to, id from BLEAT where content like ? and username in (select friend from listen where username=?) order by time DESC", (user_or_bleat, own_username))
    for row in cursor:
        username = row[0]
        url_avatar = get_avatar(username)
        timestamp = row[2]
        date_time = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        content = row[1]
        id = row[4] #for view details

        # create internal link for both other users and me who are being @, for other users, create a link, for myself, just bold it
        p1 = re.compile(r'@([\S]+)')
        at_result = p1.findall(content)  # list : ['DaisyFuentes', 'DaisyFuentes']   at_result is a list contains only one bleat
        for at_value in at_result:
            if at_value == own_username:   # the value behind @ is a myself
                # create internal link for @user
                oldstr = '@' + at_value
                newstr = "@<b> %s </b>" % at_value
                content = content.replace(oldstr, newstr, 1)
                # create internal link for @user
            else:
                cursor = conn.execute("SELECT username from user where username=?", (at_value,))
                if cursor:  # the value behind @ must be someone else
                    # create internal link for @user
                    oldstr = '@' + at_value
                    newstr = "@<a href=\"user.cgi?username=%s\"><b> %s </b></a>" % (at_value, at_value)
                    content = content.replace(oldstr, newstr, 1)
                    # create internal link for @user
                cursor.close()
        content = create_topic_link(content)
        # create internal link for both other users and me who are being @, for other users, create a link, for myself, just bold it

        reply_to = row[3]
        post_or_participate = ""
        if not reply_to:
            post_or_participate = "posted"
        else:
            post_or_participate = "participated"

        html += """
             <div class="row">
                <div class="col-sm-offset-1">
                     <h4><a href=user.cgi?username=%s>%s %s </a></h4>
                     <p><small><b> %s </b> at %s</small></p>
                     <p>%s</p>
                     <p><a class="btn btn-default" href="detail.cgi?bleatID=%s" role="button">View details &raquo;</a></p>
                </div>
             </div><br>
             """ % (username, url_avatar, username, post_or_participate, date_time, content, id)
    html += "<hr>"
    if cursor:
        cursor.close()

    cursor = conn.execute("SELECT username, content, time, in_reply_to, id from bleat where content like ? and username!=? and username not in (select friend from listen where username=?) order by time DESC", (user_or_bleat, own_username, own_username))
    html += "<h4>Result from others:</h4>"
    for row in cursor:
        username = row[0]
        url_avatar = get_avatar(username)
        timestamp = row[2]
        date_time = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        content = row[1]
        id = row[4] #for view details

        # create internal link for both other users and me who are being @, for other users, create a link, for myself, just bold it
        p2 = re.compile(r'@([\S]+)')
        at_result = p2.findall(content)  # list : ['DaisyFuentes', 'DaisyFuentes']   at_result is a list contains only one bleat
        for at_value in at_result:
            if at_value == own_username:   # the value behind @ is a myself
                # create internal link for @user
                oldstr = '@' + at_value
                newstr = "@<b> %s </b>" % at_value
                content = content.replace(oldstr, newstr, 1)
                # create internal link for @user
            else:
                cursor = conn.execute("SELECT username from user where username=?", (at_value,))
                if cursor:  # the value behind @ must be someone else
                    # create internal link for @user
                    oldstr = '@' + at_value
                    newstr = "@<a href=\"user.cgi?username=%s\"><b> %s </b></a>" % (at_value, at_value)
                    content = content.replace(oldstr, newstr, 1)
                    # create internal link for @user
                cursor.close()
        content = create_topic_link(content)
        # create internal link for both other users and me who are being @, for other users, create a link, for myself, just bold it

        reply_to = row[3]
        post_or_participate = ""
        if not reply_to:
            post_or_participate = "posted"
        else:
            post_or_participate = "participated"

        html += """
             <div class="row">
                <div class="col-sm-offset-1">
                     <h4><a href=user.cgi?username=%s>%s %s </a></h4>
                     <p><small><b> %s </b> at %s</small></p>
                     <p>%s</p>
                     <p><a class="btn btn-default" href="detail.cgi?bleatID=%s" role="button">View details &raquo;</a></p>
                </div>
             </div><br>
             """ % (username, url_avatar, username, post_or_participate, date_time, content, id)
    if cursor:
        cursor.close()
    conn.close()
    html += "</div></div>"
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
                <li> <a href="friend.cgi">Friends</a> </li>

                <li> <a href="relate.cgi">@Related</a> </li>
                <li> <a href="participate.cgi">Participated</a> </li>
                <li> <a href="comment.cgi">My Commented Posts</a> </li>
            </ul>
            <form method="get" action="search.cgi" class="navbar-form navbar-left" role="search">
                <div class="form-group">
                  <input type="text" name="user_or_bleat" class="form-control" placeholder="Search User Or Bleat">
                </div>
                <button type="submit" class="btn btn-default">Search</button>
            </form>
            <ul class="nav navbar-nav navbar-right">
                <li><a href="bitter.cgi?action=logout">Logout</a></li>
               <li><a href="views/about.html">About</a></li>
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
    user_or_bleat = parameters.getvalue('user_or_bleat')
    if not user_or_bleat:
        print """Content-Type: text/html

        <!DOCTYPE html>
        <html lang="en">
        <head>Bitter</head>
        <body><h1>Please give the name you want to search !</h1></body>
        <html>
        """
        exit(0)
    flag_logout = 0
    debug = 1

    # for debugging
    #para = ""
    # for debugging

    main()


