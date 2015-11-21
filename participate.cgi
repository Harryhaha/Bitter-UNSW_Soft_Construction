#!C:\Python27\python.exe
import cgi, cgitb, glob, time, os, sqlite3, Cookie, datetime, re

def main():
    global cookie
    global parameters
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
    print combine()
    #print comment_page()
    print page_trailer(parameters)

def redirect(url):
    return "Location: %s" % url


def create_internal_link_for_bleat_content(content, self_username, conn):
    # create internal link for both other users and me who are being @, for other users, create a link, for myself, just bold it
    p = re.compile(r'@([\S]+)')
    at_result = p.findall(content)  # list : ['DaisyFuentes', 'DaisyFuentes']   at_result is a list contains only one bleat
    for at_value in at_result:
        if at_value == self_username:   # the value behind @ is a myself
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
    p2 = re.compile(r'#([\S]+)')
    at_result = p2.findall(content)  # list : ['DaisyFuentes', 'DaisyFuentes']   at_result is a list contains only one bleat
    for at_value in at_result:
        oldstr = '#' + at_value
        newstr = "<a href=\"search.cgi?user_or_bleat=%23" + at_value + "\"><b>#" + at_value + "</b></a>"
        content = content.replace(oldstr, newstr, 1)
    return content
    # create internal link for both other users and me who are being @, for other users, create a link, for myself, just bold it

def get_avatar(username):
    avatar = ""
    conn = sqlite3.connect('users.db')
    cursor = conn.execute("SELECT profile from user where username=?;", (username ,))
    for row in cursor:
        avatar = row[0]
    if avatar:
        url_avatar = "<img src=\"%s\" alt=\"Bitter\" class=\"img-circle\" height=\"20px\" width=\"20px\">" % avatar
    else:
        url_avatar = "<img src=\"avatar/default.jpg\" alt=\"Bitter\" class=\"img-circle\" height=\"20px\" width=\"20px\">"
    conn.close()
    return url_avatar

def comment_page(side):
    global cookie
    global flag_logout
    global thenameofuser
    self_username = ''
    string_cookie = os.environ.get('HTTP_COOKIE')
    if string_cookie:
        cookie.load(string_cookie)
        if 'sid' in cookie:
            self_username = cookie['sid'].value
    conn = sqlite3.connect('users.db')
    #BLEAT: id, username content time longitude latitude in_reply_to
    cursor = None
    if side == 'left':
        cursor = conn.execute("SELECT username, content, time, longitude, latitude, id, in_reply_to from bleat where username=? and in_reply_to is not null order by time DESC", (self_username,))
    else:
        cursor = conn.execute("SELECT username, content, time, longitude, latitude, id, in_reply_to from bleat where in_reply_to in (select id from bleat where username=?) and in_reply_to is not null order by time DESC", (self_username,))
    comments_detail = ""
    for row in cursor:
        other_reply_me = row[6]
        other_username = row[0]
        other_content = row[1]
        other_content = create_internal_link_for_bleat_content(other_content, self_username, conn)
        other_time = row[2]
        other_time = datetime.datetime.fromtimestamp(other_time).strftime('%Y-%m-%d %H:%M:%S')
        other_longitude = row[3]
        other_latitude = row[4]
        other_time_id = row[5]
        cursor2 = conn.execute("SELECT username, content, time, longitude, latitude, id, in_reply_to from bleat where id=?", (other_reply_me,))
        username, content, time, longitude, latitude, id, in_reply_to, post_or_participate, response_header = '','','',0,0,0,0,'',''

        for row2 in cursor2:  # only one record!
            username = row2[0] #row[0]
            content = row2[1]
            content = create_internal_link_for_bleat_content(content, self_username, conn)
            timestamp = row2[2]
            time = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            longitude = row2[3]
            latitude = row2[4]
            id = row2[5]
            in_reply_to = row2[6]
            if in_reply_to:
                post_or_participate = "participated"
            else:
                post_or_participate = "posted"

            if side == 'right':
                if other_username == self_username:
                    response_header = "%s <b>My response:</b>" % get_avatar(self_username)
                else:
                    response_header = "<a href=\"user.cgi?username=%s\">%s <b> %s</b></a> <b>'s response:</b>" % (other_username, get_avatar(other_username), other_username)

        if side == 'left':
            comments_detail += """
            <div class="panel panel-info">
              <div class="panel-heading"><b>The bleat that I have responded:&nbsp;&nbsp;&nbsp; <a href="detail.cgi?bleatID=%s">Click here to see all the details</a></b></div>
                  <div class="panel-body">
                      <div class="col-md-11 col-sm-offset-1">
                          <div class="row">
                             <h5><a href="user.cgi?username=%s">%s <b> %s </b></a></h5><p><small><b>time:</b>&nbsp;&nbsp;<b> %s </b> at %s &nbsp;&nbsp;&nbsp;&nbsp; <b>Location:</b> longitude: %s &nbsp;&nbsp; Latitude: %s</small></p>
                          </div>
                          <div class="row"> %s </div>
                          <div class="row">
                                <hr><h5>%s <b>My response:</b></h5>
                          </div>
                          <div class="row">
                              <p><small><b>time:</b>&nbsp;&nbsp;<b>participated</b> at %s &nbsp;&nbsp;&nbsp;&nbsp; <b>Location:</b> longitude: %s &nbsp;&nbsp; Latitude: %s</small></p>
                          </div>
                          <div class="row"> %s </div>
                      </div>
                  <br>
                  </div>
            </div>
            <hr><br>
            """ % (id, username, get_avatar(username), username, post_or_participate, time, longitude, latitude, content, get_avatar(self_username), other_time, other_longitude, other_latitude, other_content)
        else:
            comments_detail += """
            <div class="panel panel-info">
              <div class="panel-heading"><b>The bleat that responded to me:&nbsp;&nbsp;&nbsp; <a href="detail.cgi?bleatID=%s">Click here to see all the details</a></b></div>
                  <div class="panel-body">
                      <div class="col-md-11 col-sm-offset-1">
                          <div class="row">
                              <h5>%s <b> Me </b></h5><p><small><b>time:</b>&nbsp;&nbsp;<b> %s </b> at %s &nbsp;&nbsp;&nbsp;&nbsp; <b>Location:</b> longitude: %s &nbsp;&nbsp; Latitude: %s</small></p>
                          </div>
                          <div class="row"> %s </div>
                          <div class="row">
                                <hr><h5> %s </h5>
                          </div>
                          <div class="row">
                              <p><small><b>time:</b>&nbsp;&nbsp;<b>participated</b> at %s &nbsp;&nbsp;&nbsp;&nbsp; <b>Location:</b> longitude: %s &nbsp;&nbsp; Latitude: %s</small></p>
                          </div>
                          <div class="row"> %s </div>

                          <div class="row">
                          %s
                          </div>

                      </div>
                  <br>
                  </div>
            </div>
            <hr><br>
            """ % (id, get_avatar(self_username), post_or_participate, time, longitude, latitude, content, response_header, other_time, other_longitude, other_latitude, other_content, thenameofuser)
        cursor2.close()
    cursor.close()
    conn.close()
    return comments_detail

def combine():
    html = """
    <div class="container">
        <div class="row">
            <div class="col-md-6">
                %s
            </div>
            <div class="col-md-6">
                %s
            </div>
        </div>
    </div>
    """ % (comment_page('left'), comment_page('right'))
    return html

#
# HTML placed at the top of every page
#
def page_header():
    global cookie
    global content
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

                <li> <a href="relate.cgi">@Related</a></li>
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
    cgitb.enable()
    parameters = cgi.FieldStorage()
    cookie = Cookie.SimpleCookie()
    debug = 1
    flag_logout = 0
    # just for debug
    thenameofuser = ''
    #just for debug

    main()



