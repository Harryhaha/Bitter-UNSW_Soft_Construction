#!C:\Python27\python.exe
import cgi, cgitb, glob, time, os, sqlite3, Cookie, datetime, re, smtplib
from email.mime.text import MIMEText
from operator import itemgetter, attrgetter

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
    global bleat_id
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

    # self post bleat handle
    #BLEAT: id, username content time longitude latitude in_reply_to
    if parameters.getvalue('content'):
        global content
        global flag_post_successfully
        content += parameters.getvalue('content')

        flag_post_successfully = 1

        string_cookie = os.environ.get('HTTP_COOKIE')
        cookie.load(string_cookie)
        username = cookie['sid'].value
        content = parameters.getvalue('content')

        #their username is mentioned in a bleat
        conn = sqlite3.connect('users.db')
        p = re.compile(r'@([\S]+)')
        at_result = p.findall(content)
        for at_value in at_result:
            cursor = conn.execute("SELECT username, email from user where username=?", (at_value,))
            for row in cursor: # only one record
                username_reply_to = row[0]
                if username_reply_to:
                    email = row[1]
                    message = """
                        Hi, the user %s mentioned you in bleat just now :)
                    """ % username
                    subject = "Bleat mention from Bitter"
                    send_email(email, message, subject)
            cursor.close()
        #their username is mentioned in a bleat

        time_current = time.time()
        longitude = parameters.getvalue('longitude')
        latitude = parameters.getvalue('latitude')

        if parameters.getvalue('current_bleat_id'):
            in_reply_to = parameters.getvalue('current_bleat_id')
        else:
            in_reply_to = bleat_id

        #someone replies to one of their bleets
        email = ""
        cursor = conn.execute("SELECT username, email from user where username=(select username from bleat where id=?)", (in_reply_to, ))
        for row in cursor:
            email = row[1]
        message = """
            Hi, the user %s replied to you in bleat just now :)
        """ % username
        subject = "Bleat reply notification from Bitter"
        send_email(email, message, subject)
        cursor.close()
        #someone replies to one of their bleets

        # insert
        cursor = conn.execute("SELECT max(id) from bleat")
        id_largest = 0
        for row in cursor:
            id_largest = row[0]
        id = id_largest + 1

        conn.execute("INSERT INTO BLEAT (ID, USERNAME, CONTENT, TIME, LONGITUDE, LATITUDE, IN_REPLY_TO) \
                 VALUES (?, ?, ?, ?, ?, ?, ?);", (id, username, content, time_current, longitude, latitude, in_reply_to))
        conn.commit()
        conn.close()

    # self post bleat handle
    print page_header()
    print fetch_all_bleats()
    print page_trailer(parameters)

def redirect(url):
    return "Location: %s" % url

def get_avatar(username):
    avatar = ""
    conn = sqlite3.connect('users.db')
    cursor = conn.execute("SELECT profile from user where username=?;", (username,))
    for row in cursor:
        avatar = row[0]
    if avatar:
        url_avatar = "<img src=\"%s\" alt=\"Bitter\" class=\"img-circle\" height=\"20px\" width=\"20px\">" % avatar
    else:
        url_avatar = "<img src=\"avatar/default.jpg\" alt=\"Bitter\" class=\"img-circle\" height=\"20px\" width=\"20px\">"
    conn.close()
    return url_avatar

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

# recursively fetch the top bleat for that comment
def fetch_top_bleat(bleat_id, conn):
    #BLEAT: id, username content time longitude latitude in_reply_to
    cursor = conn.execute("SELECT id, in_reply_to from bleat where id=?", (bleat_id,)) #only one record!
    for row in cursor:
        if not row[1]:
            cursor.close()
            return bleat_id
    cursor = conn.execute("SELECT id, in_reply_to from bleat where id=?", (bleat_id,)) #only one record!
    for row in cursor:
        return fetch_top_bleat(row[1], conn)

def fetch_all_comments(all_comments_list, top_bleat_id, conn, self_username):
    #BLEAT: id, username content time longitude latitude in_reply_to
    cursor = conn.execute("SELECT id, username, content, time, longitude, latitude, in_reply_to from bleat where in_reply_to=?", (top_bleat_id,)) #many record!
    if not cursor:
        return all_comments_list

    for row in cursor:
        id = row[0]
        user = row[1]
        content = row[2]
        content = create_internal_link_for_bleat_content(content, self_username, conn)
        timestamp = row[3] #numeric type
        #####################
        if row[4]:
            longitude = row[4]
        else:
            longitude = 0.0
        if row[5]:
            latitude = row[5]
        else:
            latitude = 0.0
        in_reply_to = row[6] #numeric

        username_reply_to = ""
        cursor2 = conn.execute("SELECT username from bleat where id=?", (in_reply_to,))
        if cursor2:
            for row in cursor2:
                username_reply_to = row[0]
        cursor2.close()

        #format:  time, id, username, content, longitude, latitude, in_reply_to, username_reply_to
        single_comment_details = [timestamp, id, user, content, longitude, latitude, in_reply_to, username_reply_to]
        all_comments_list.append(single_comment_details)

        fetch_all_comments(all_comments_list, id, conn, self_username)
    return all_comments_list


def fetch_all_bleats(): #flag_login_successfully should be change to session check
    global cookie
    global flag_logout
    global flag_post_successfully
    global flag_login_successfully
    global bleat_id
    global form_string
    prompt_post_successfully = ""
    if flag_post_successfully == 1:
        prompt_post_successfully = "post successfully !"
    self_username = ''
    string_cookie = os.environ.get('HTTP_COOKIE')
    if string_cookie:
        cookie.load(string_cookie)
        if 'sid' in cookie:
            self_username = cookie['sid'].value

    conn = sqlite3.connect('users.db')
    #BLEAT: id, username content time longitude latitude in_reply_to
    top_bleat_id = fetch_top_bleat(bleat_id, conn)
    top_bleat_username = ""
    cursor = conn.execute("SELECT username, content, time, longitude, latitude from bleat where id=?", (top_bleat_id,))
    top_bleat_username, top_bleat_content, top_bleat_time, top_bleat_longitude, top_bleat_latitude = '', '', '', '', ''
    for row in cursor:
        top_bleat_username = row[0]
        top_bleat_content = row[1]
        top_bleat_content = create_internal_link_for_bleat_content(top_bleat_content, self_username, conn)
        top_bleat_time = row[2]
        top_bleat_time = datetime.datetime.fromtimestamp(top_bleat_time).strftime('%Y-%m-%d %H:%M:%S')
        top_bleat_longitude = row[3]
        if not top_bleat_longitude:
            top_bleat_longitude = ""
        else:
            top_bleat_longitude = str(top_bleat_longitude)

        top_bleat_latitude = row[4]
        if not top_bleat_latitude:
            top_bleat_latitude = ""
        else:
            top_bleat_latitude = str(top_bleat_latitude)
    cursor.close()

    all_comments_list = []
    all_comments_list = fetch_all_comments(all_comments_list, top_bleat_id, conn, self_username)
    all_comments_ordered_list = sorted(all_comments_list, key=itemgetter(0))

    final_comment_string = ""
    #format:  time, id, username, content, longitude, latitude, in_reply_to, username_reply_to
    single_comment_id = 1
    for comment in all_comments_ordered_list:
        #comment_string = ""
        #date_time = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        comment[0] = datetime.datetime.fromtimestamp(comment[0]).strftime('%Y-%m-%d %H:%M:%S')
        if comment[4] == 0.0:
            comment[4] = ""
        else:
            comment[4] = str(comment[4])

        if comment[5] == 0.0:
            comment[5] = ""
        else:
            comment[5] = str(comment[5])

        comment_header = ""
        left_user = ""
        right_user = ""
        if comment[7] == top_bleat_username:
            if comment[2] == self_username:
                comment_header = "%s <b> %s: </b>" % (get_avatar(comment[2]), comment[2])
            else:
                comment_header = """
                <a href="user.cgi?username=%s">%s <b> %s: </b></a>
                """ % (comment[2], get_avatar(comment[2]), comment[2])
        else:
            if comment[2] == self_username:
                left_user = "%s <b> %s </b>" % (get_avatar(comment[2]), comment[2])
            else:
                left_user = "<a href=\"user.cgi?username=%s\">%s <b> %s </b></a>" % (comment[2], get_avatar(comment[2]), comment[2])

            if comment[7] == self_username:
                right_user = "%s <b> %s </b>" % (get_avatar(comment[7]), comment[7])
            else:
                right_user = "<a href=\"user.cgi?username=%s\">%s <b> %s </b></a>" % (comment[7], get_avatar(comment[7]), comment[7])

            comment_header = "%s @ %s" % (left_user, right_user)

        #comment_string = comment[2] + user_to_reply + comment[3] + comment[0] + comment[4] + comment[5]
        final_comment_string += """
        <div id="comment%s">
            <div class="row">
                <hr>
                <h5> %s &nbsp;&nbsp
                    <small><b>time:</b>&nbsp;&nbsp;<b>participated</b> at %s &nbsp;&nbsp;&nbsp;&nbsp; <b>Location:</b> longitude: %s &nbsp;&nbsp; Latitude: %s </small>
                </h5>
            </div>
            <div class="row">
                  %s <button class="comment btn btn-primary btn-sm pull-right">comment</button>
            </div>


            <div style="display:none;" class="comment_form row">
                  %s
            </div>
        </div>

        <script type="text/javascript">
            var $hidden_element_store_current_username= $("<input type='hidden' name='current_bleat_id' value='%s'>");
            $("div#comment%s").children("div.comment_form").children().children().append($hidden_element_store_current_username);
        </script>
        """ % (single_comment_id, comment_header, comment[0], comment[4], comment[5], comment[3], form_string, comment[1], single_comment_id)
        single_comment_id += 1

    bleat_detail_header = ""
    if top_bleat_username == self_username:
        bleat_detail_header = "%s <b> %s </b>" % (get_avatar(top_bleat_username), top_bleat_username)
    else:
        bleat_detail_header = "<a href=\"user.cgi?username=%s\">%s <b> %s </b></a>" % (top_bleat_username, get_avatar(top_bleat_username), top_bleat_username)
    # fetch all of comments here
    bleat_detail = """
    <div class="col-md-10 col-sm-offset-1">
          <div class="row">
              <h3> %s </h3><p><small><b>time:</b>&nbsp;&nbsp;<b>posted</b> at %s &nbsp;&nbsp;&nbsp;&nbsp; <b>Location:</b> longitude: %s &nbsp;&nbsp; Latitude: %s</small></p>
          </div>
          <div class="row">
              %s
          </div>

          <div class="row">
              %s
          </div>
          <div class="row">
                <b>all comments below:</b>
          </div>

          %s
    <br>
    </div>
    """ % (bleat_detail_header, top_bleat_time, top_bleat_longitude, top_bleat_latitude, top_bleat_content, form_string, final_comment_string)

    if (flag_login_successfully == 1 or self_username != '') and flag_logout != 1: # has login in
        return"""
        <div class="container">
            <div class="row">
                <div class="col-md-1"></div>
                <div class="col-md-10">
                      <div class="panel panel-info">
                          <div class="panel-heading">Bleat details</div>
                          <div class="panel-body">
                           %s
                          </div>
                      </div>
                </div>
            </div>
      </div>
       """ % bleat_detail

    else:
        return ""
    #<!-- <div>%d</div> <div>%s</div> -->

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
    <script type="text/javascript">
    $(document).ready(function(){
      $(".comment").click(function(){
          $(this).parent().parent().children("div.comment_form").toggle("fast");
          console.log($(this).parent().parent())
      });
    });
    </script>
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
    cgitb.enable()
    parameters = cgi.FieldStorage()
    bleat_id = parameters.getvalue('bleatID') # which is string, but in database it is numeric
    cookie = Cookie.SimpleCookie()
    debug = 1
    flag_logout = 0
    flag_post_successfully = 0
    flag_login_successfully = 0
    form_string = """
    <form method="post" action="detail.cgi?bleatID=%s" class="form-horizontal">
        <fieldset>
            <!-- Textarea -->
            <div class="form-group">
                <div class="col-md-12">
                    <label class="control-label">My comment:</label>
                    <div class="controls">
                        <textarea class="form-control" rows="4" name="content"></textarea>
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
                <div class="col-sm-6"><button type="submit" class="btn btn-primary btn-sm pull-right">Post it!</button></div>
            </div>
        </fieldset>
    </form>
    """ % bleat_id

    # just for debugging
    content = "harry's content is: "
    # just for debugging
    main()

