#!C:\Python27\python.exe
import cgi, cgitb, glob, time, os, sqlite3, Cookie, datetime, re

def main():
    global cookie
    cgitb.enable()
    parameters = cgi.FieldStorage()

    # logout handle
    if parameters.getvalue('action') == 'logout' and not parameters.getvalue('login'):
        global flag_logout
        flag_logout = 1

        #delete related session here
        cookie['sid'] = ''
        cookie['sid']['expires'] = 'Thu, 01 Jan 1970 00:00:00 GMT'
        print cookie

        #print "Set-Cookie: sid=\'\'"
        #delete related session here
        prompt_logout = "logout successfully."
        redirect('./bitter.cgi')
    else:
        prompt_logout = ""

    # logout handle

    print page_header()

    print self_bleat()
    #print bleats_page()
    print page_trailer(parameters)

def redirect(url):
    return "Location: %s" % url

# create internal link for # topic, just return back to the original bleat
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

def self_bleat(): #flag_login_successfully should be change to session check
    global cookie
    global flag_logout
    global flag_login_successfully

    self_username = ''
    string_cookie = os.environ.get('HTTP_COOKIE')
    if string_cookie:
        cookie.load(string_cookie)
        if 'sid' in cookie:
            self_username = cookie['sid'].value
    conn = sqlite3.connect('users.db')

    # at others part !
    cursor1 = conn.execute("SELECT username, content, time, in_reply_to, id from bleat where username=? and content like '%@%' order by time DESC", (self_username,))
    date_time = ""
    flag_At_others = 0
    at_others = ""
    for row in cursor1:
        flag_At_others = 0
        content = row[1]
        p1 = re.compile(r'@([\S]+)')
        at_result = p1.findall(content)  # list : ['DaisyFuentes', 'DaisyFuentes']   at_result is a list contains only one bleat
        for at_value in at_result:
            cursor2 = conn.execute("SELECT username from user where username=?", (at_value,))
            if cursor2:  # the value behind @ is a real username
                flag_At_others = 1
                # create internal link for @user
                oldstr = '@' + at_value
                newstr = "@<a href=\"user.cgi?username=%s\"><b> %s </b></a>" % (at_value, at_value)
                content = content.replace(oldstr, newstr, 1)
                # create internal link for @user
        # create internal link for # topic, just return back to the original bleat
        content = create_topic_link(content)
        if flag_At_others == 1:
            #self_username = row[0]
            url_avatar = get_avatar(self_username)
            timestamp = row[2]
            date_time = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            reply_to = row[3]
            id = row[4]
            post_or_participate = ""
            if not reply_to:
                post_or_participate = "posted"
            else:
                post_or_participate = "participated"
            at_others += """<div class="row">
                                   <h2>%s Me</h2><small><b> %s </b> at %s</small></p>\
                                   <p>%s</p>
                                   <p><a class=\"btn btn-default btn-sm\" href=\"detail.cgi?bleatID=%s\" role=\"button\">View details &raquo;</a></p>
                               </div>""" % (url_avatar, post_or_participate, date_time, content, id)

    # at me part !
    cursor2 = conn.execute("SELECT username, content, time, in_reply_to, id from bleat where content like '%@%' order by time DESC")
    at_me = ""
    flag_At_me = 0
    for row in cursor2:
        url_avatar = get_avatar(self_username)
        flag_At_me = 0
        content = row[1]
        p2 = re.compile(r'@([\S]+)')
        at_result = p2.findall(content)  # list : ['DaisyFuentes', 'DaisyFuentes']   at_result is a list contains only one bleat
        for at_value in at_result:
            if at_value == self_username:
                flag_At_me = 1
                # create bold for self_username
                oldstr = '@' + at_value
                newstr = "@<b> %s </b>" % self_username
                content = content.replace(oldstr, newstr, 1)
                # create bold for self_username
        # create internal link for # topic, just return back to the original bleat
        content = create_topic_link(content)
        if flag_At_me == 1:
            username = row[0]
            url_avatar = get_avatar(username)
            timestamp = row[2]
            date_time = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            reply_to = row[3]
            id = row[4]
            post_or_participate = ""
            if not reply_to:
                post_or_participate = "posted"
            else:
                post_or_participate = "participated"

            at_me += """<div class="row">
                                   <h2><a href=user.cgi?username=%s>%s %s</a></h2><small><b> %s </b> at %s</small></p>\
                                   <p>%s</p>
                                   <p><a class=\"btn btn-default btn-sm\" href=\"detail.cgi?bleatID=%s\" role=\"button\">View details &raquo;</a></p>
                               </div>""" % (username, url_avatar, username, post_or_participate, date_time, content, id)

    conn.close()
    if (flag_login_successfully == 1 or self_username != '') and flag_logout != 1: # has login in
        return"""
        <div class="container">
            <div class="row vdivide">
                <div class="col-md-5">

                  <br><div id="legend" class=""><legend class="">@ others</legend></div>
                      <div class="col-md-offset-1">%s</div>
                  </div>

                  <div class="col-md-1"></div>
                  <div class="col-md-6">
                  <br><div id="legend" class=""><legend class="">@ me</legend></div>
                      <div class="col-md-offset-1">%s</div>
                 </div>
            </div>
      </div>
       """ % (at_others, at_me)
    else:
        return ""
    #<!-- <div>%d</div> <div>%s</div> -->

#
# HTML placed at the top of every page
#
def page_header():
    global cookie

    #should has an empty line below.
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
#<!-- <p>sid is:%s</p><br><p>flag_login_successfully is:%d</p><br><p>string_cookie is: %s<p> -->
#sid, flag_login_successfully, string_cookie


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
    debug = 1
    flag_login_successfully = 0
    flag_logout = 0
    main()

