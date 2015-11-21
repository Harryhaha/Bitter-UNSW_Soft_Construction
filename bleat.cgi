#!C:\Python27\python.exe
# written by andrewt@cse.unsw.edu.au September 2015
# as a starting point for COMP2041/9041 assignment 2
# http://cgi.cse.unsw.edu.au/~cs2041/assignments/bitter/

import cgi, cgitb, glob, time, os, sqlite3, Cookie, datetime, re, smtplib
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
    global cookie
    cgitb.enable()
    parameters = cgi.FieldStorage()      	#FieldStorage(None, None, [])  now
    self_username = ""
    string_cookie = os.environ.get('HTTP_COOKIE')
    if string_cookie:
        cookie.load(string_cookie)
        if 'sid' in cookie:
            self_username = cookie['sid'].value

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

    # self post bleat handle
    #BLEAT: id, username content time longitude latitude in_reply_to
    if parameters.getvalue('content'):
        global flag_post_successfully
        flag_post_successfully = 1
        content = parameters.getvalue('content')

        conn = sqlite3.connect('users.db')
        #their username is mentioned in a bleat
        p = re.compile(r'@([\S]+)')
        at_result = p.findall(content)
        for at_value in at_result:
            cursor = conn.execute("SELECT username, email from user where username=?", (at_value,))
            for row in cursor: # only one record
                username = row[0]
                if username:
                    email = row[1]
                    message = """
                        Hi, the user %s mentioned you in bleat just now :)
                    """ % self_username
                    subject = "Bleat mention from Bitter"
                    send_email(email, message, subject)
            cursor.close()
        #their username is mentioned in a bleat

        time_current = time.time()
        longitude = parameters.getvalue('longitude')
        latitude = parameters.getvalue('latitude')
        # insert

        cursor = conn.execute("SELECT max(id) from bleat")
        id_largest = 0
        for row in cursor:
            id_largest = row[0]
        id = id_largest + 1

        conn.execute("INSERT INTO BLEAT (ID, USERNAME, CONTENT, TIME, LONGITUDE, LATITUDE) \
                 VALUES (?, ?, ?, ?, ?, ?);", (id, self_username, content, time_current, longitude, latitude))
        conn.commit()
        conn.close()

    if parameters.getvalue('myBleatId'):
        global flag_delete_bleat_successfully
        flag_delete_bleat_successfully = 1
        myBleatId_to_be_deleted = parameters.getvalue('myBleatId')
        conn = sqlite3.connect('users.db')
        conn.execute("DELETE from bleat where id=?;", (myBleatId_to_be_deleted,))
        conn.commit()
        conn.close()

    # self post bleat handle

    print page_header()  #header actually should be processd, it contain home, about, register, and username sign in with password
    print self_bleat()
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
    global flag_post_successfully
    global flag_delete_bleat_successfully
    prompt_post_successfully = ""
    if flag_post_successfully == 1:
        prompt_post_successfully = "post successfully !"
    prompt_delete_bleat_successfully = ""
    if flag_delete_bleat_successfully == 1:
        prompt_delete_bleat_successfully = "delete successfully"
    username = ''
    string_cookie = os.environ.get('HTTP_COOKIE')
    if string_cookie:
        cookie.load(string_cookie)
        if 'sid' in cookie:
            username = cookie['sid'].value

    conn = sqlite3.connect('users.db')
    cursor = conn.execute("SELECT username, content, time, id from bleat where username=? and in_reply_to is null order by time DESC", (username,))
    self_bleats = ""
    date_time = ""
    for row in cursor:
        #user = row[0]
        url_avatar = get_avatar(username)

        timestamp = row[2]
        date_time = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        content = row[1]
        id = row[3] #for view details

        # create internal link for both other users and me who are being @, for other users, create a link, for myself, just bold it
        p1 = re.compile(r'@([\S]+)')
        at_result = p1.findall(content)  # list : ['DaisyFuentes', 'DaisyFuentes']   at_result is a list contains only one bleat
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
        # create internal link for both other users and me who are being @, for other users, create a link, for myself, just bold it
        # create internal link for # topic, just return back to the original bleat
        content = create_topic_link(content)
        self_bleats += """<div class="row">
                               <h2>%s Me</h2><small>posted at %s</small></p>\
                               <p>%s</p>
                                <p>
                                   <form role="search" method="post" id="" action="">
                                   <a class="btn btn-default btn-sm" href="detail.cgi?bleatID=%s" role="button">View details &raquo;</a>
                                    &nbsp;&nbsp;&nbsp;
                                    <input type="hidden" name="myBleatId" value="%d">
                                    <button type="submit" class="btn btn-danger btn-sm">Delete</button>
                                   </form>
                               </p>
                        </div>""" % (url_avatar, date_time, content, id, id)
    if cursor:
        cursor.close()

    #if (username != "" or flag_login_successfully == 1) and flag_logout == 0: #has already login
    cursor3 = conn.execute("SELECT username, content, time, id from bleat where (username in (select friend from listen where username=?)) and in_reply_to is null order by time DESC",(username,))
    #else:
        #username content time longitude latitude in_reply_to
        #cursor = conn.execute("SELECT username, content from bleat order by time DESC")

    users_bleats = ""
    for row in cursor3:
        user = row[0]
        url_avatar = get_avatar(user)
        timestamp = row[2]
        date_time = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        id = row[3] #for view details
        content = row[1]

        # create internal link for both other users and me who are being @, for other users, create a link, for myself, just bold it
        p2 = re.compile(r'@([\S]+)')
        at_result = p2.findall(content)  # list : ['DaisyFuentes', 'DaisyFuentes']   at_result is a list contains only one bleat
        for at_value in at_result:
            if at_value == username:   # the value behind @ is a myself
                # create internal link for @user
                oldstr = '@' + at_value
                newstr = "@<b> %s </b>" % at_value
                content = content.replace(oldstr, newstr, 1)
                # create internal link for @user
            else:
                cursor4 = conn.execute("SELECT username from user where username=?", (at_value,))
                if cursor4:  # the value behind @ must be someone else
                    # create internal link for @user
                    oldstr = '@' + at_value
                    newstr = "@<a href=\"user.cgi?username=%s\"><b> %s </b></a>" % (at_value, at_value)
                    content = content.replace(oldstr, newstr, 1)
                    # create internal link for @user
                cursor4.close()
        # create internal link for both other users and me who are being @, for other users, create a link, for myself, just bold it
        # create internal link for # topic, just return back to the original bleat
        content = create_topic_link(content)
        users_bleats += """<div class="row">
                               <h2><a href=user.cgi?username=%s>%s %s</a></h2><small>posted at %s</small></p>
                               <p>%s</p>
                               <p><a class="btn btn-default btn-sm" href="detail.cgi?bleatID=%s" role="button">View details &raquo;</a></p>
                        </div>""" % (user, url_avatar, user, date_time, content, id)
    if cursor3:
        cursor3.close()
    conn.close()
    if (flag_login_successfully == 1 or username != '') and flag_logout != 1: # has login in

        return"""
        <div class="container">
            <div class="row vdivide">
                <div class="col-md-5">
                  <form method="post" action="" class="form-horizontal">
                    <fieldset>
                        <br><div id="legend" class=""><legend class="">Post my bleat! &nbsp;&nbsp;&nbsp;&nbsp;
                        <b>%s</b></legend></div>
                        <!-- Textarea -->
                        <div class="form-group">
                            <div class="col-md-12">
                                <label class="control-label">Content</label>
                                <div class="controls">
                                    <textarea maxlength="142" class="form-control" rows="7" name="content"></textarea>
                                </div>
                            </div>
                        </div>
                        <!-- Two text -->
                        <div class="form-group">
                            <div class="col-md-6">
                                <label class="sr-only" for="exampleInputAmount">longitude</label>
                                <div class="input-group">
                                  <div class="input-group-addon">longitude</div>
                                  <input type="text" class="form-control" name="longitude" id="longitude" placeholder="optional">
                                </div>
                            </div>

                            <div class="col-md-6">
                                <label class="sr-only" for="exampleInputAmount">latitude</label>
                                <div class="input-group">
                                  <div class="input-group-addon">latitude</div>
                                  <input type="text" class="form-control" name="latitude" id="latitude" placeholder="optional">
                                </div>
                            </div>
                        </div>
                        <!-- upload and submit button -->
                        <div class="form-group">
                            <div class="col-sm-6"><input type="file" id="exampleInputFile"></div>
                                     <!--   <input class="input-file" id="fileInput" type="file">
                                            <button type="submit" class="btn btn-primary">Next user &raquo;</button>
                                            <input type="file" id="exampleInputFile">
                                            <button type="file" class="btn btn-info pull-left">File</button>
                                     -->
                            <div class="col-sm-6"><button type="submit" class="btn btn-primary btn-sm pull-right">Post it!</button></div>
                        </div>
                    </fieldset>
                  </form>

                  <br><div id="legend" class=""><legend class="">My Post below !&nbsp;&nbsp;&nbsp; <small style="color:red;">%s</small></legend>  </div>
                      <div class="col-md-offset-1">%s</div>
                  </div>

                  <div class="col-md-2"></div>
                  <div class="col-md-5">
                  <br><div id="legend" class=""><legend class="">My friends' bleats !</legend></div>

                    %s

                 </div>
            </div>
      </div>
       """ % (prompt_post_successfully, prompt_delete_bleat_successfully, self_bleats, users_bleats)

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
    flag_create_account_successfully = 0
    flag_login_successfully = 0
    flag_logout = 0
    flag_post_successfully = 0
    flag_delete_bleat_successfully = 0
    main()

