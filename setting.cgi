#!C:\Python27\python.exe
import cgi, cgitb, glob, os, sqlite3, Cookie, smtplib, time
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

def result_change_password(self_username, parameters):
    global flag_change_password_successfully
    if parameters.getvalue('realChangePassword'):
        current_password = parameters.getvalue('current_password')
        new_password = parameters.getvalue('new_password')

        conn = sqlite3.connect('users.db')
        cursor = conn.execute("SELECT password from user where username=?;", (self_username ,))
        real_password = ""
        for row in cursor:
            real_password = row[0]
        if real_password == current_password:
            flag_change_password_successfully = 1
            conn.execute("update user SET password=? WHERE username = ?", (new_password, self_username))
        conn.commit()
        conn.close()
    return

def real_change_password(self_username, parameters):
    global script_change_password
    global flag_real_change_password_status
    flag_contain = False
    index_delete = -1
    if parameters.getvalue('startChangePassword'):
        username = parameters.getvalue('username')
        timehash = parameters.getvalue('id')

        f = open('tmp_user_hash', 'r')
        f.seek(0)
        result_list = f.readlines()
        for i in range(len(result_list)):
            username_timehash = result_list[i].split()
            if username_timehash and username_timehash[0] == username and username_timehash[1] == str(timehash):
                flag_contain = True
                index_delete = i
                break
        f.close()
        if flag_contain == True:
            flag_real_change_password_status = 1
            del result_list[index_delete]
            tmp_file = "\n".join(result_list)
            tmp_file += "\n"
            f = open('tmp_user_hash', 'w')
            f.write(tmp_file)
            f.seek(0)
            f.close()

            script_change_password = """

                <script type="text/javascript">
                    $(document).ready(function(){
                           $("#changePassword").parent().parent().parent().parent().parent().append('\
                           <div class="container change_password">\
                               <form method="post" action="" class="form-horizontal">\
                                      <input type="hidden" name="realChangePassword" value="true">\
                                        \
                                      <div class="form-group">\
                                        <label for="current_password" class="col-sm-2 control-label">Current Password</label>\
                                        <div class="col-sm-8">\
                                          <input type="current_password" class="form-control" name="current_password" value="" id="current_password" placeholder="current password">\
                                        </div>\
                                      </div>\
                                        \
                                      <div class="form-group">\
                                        <label for="new_password" class="col-sm-2 control-label">New Password</label>\
                                        <div class="col-sm-8">\
                                          <input type="new_password" class="form-control" name="new_password" value="" id="new_password" placeholder="new password">\
                                        </div>\
                                      </div>\
                                        \
                                      <div class="form-group">\
                                        <div class="col-sm-8 col-sm-offset-2">\
                                           <button type="submit" class="btn btn-primary">Confirm Password</button>\
                                        </div>\
                                      </div>\
                                     <hr>\
                                </form>\
                           </div> ');
                    });
                </script>
            """

def change_password(self_username, parameters):
    global flag_start_change_password
    if parameters.getvalue('changePassword'):
        timehash = hash(int(time.time()))

        flag_contain = False
        f = open('tmp_user_hash', 'w')  # for password change
        if f:
            f.close()
            f = open('tmp_user_hash', 'r')
            f.seek(0)
            result_list = f.readlines()
            for i in range(len(result_list)):
                username_timehash = result_list[i].split()
                if username_timehash[0] == self_username:
                    result_list[i] = self_username + " " + timehash
                    flag_contain = True
                    break
            f.close()
        else:
            f.close()

        if flag_contain == True:
            tmp_file = "\n".join(result_list)
            tmp_file += "\n"
            f = open('tmp_user_hash', 'w')
            f.write(tmp_file)
            f.seek(0)
            f.close()
        else:
            f = open('tmp_user_hash', 'a')
            usr_time = "%s %s\n" % (self_username, str(timehash))
            f.write(usr_time)
            f.seek(0)
            f.close()

        conn = sqlite3.connect('users.db')
        cursor = conn.execute("SELECT email from user where username=?;", (self_username,))
        my_email = ""
        for row in cursor: #only one record
            my_email = row[0]
        #send a confirmation email to the new user
        message = """
            Hi, %s, I am bitter. Please click below link to complete the your password change.\n
            http://localhost/cgi-bin/setting.cgi?startChangePassword=true&username=%s&id=%s
        """ % (self_username, self_username, str(timehash))
        subject = 'Password change from Bitter'
        send_email(my_email, message, subject)
        conn.close()
        flag_start_change_password = 1
        #send a confirmation email to the new user
    return

def delete_account(self_username, parameters):
    global cookie
    if parameters.getvalue('delete'):
        delete_username = parameters.getvalue('delete')
        conn = sqlite3.connect('users.db')
        conn.execute("delete from user where username=?;", (delete_username,))
        conn.execute("delete from bleat where username=?;", (delete_username,))
        conn.execute("delete from listen where username=?;", (delete_username,))
        conn.commit()
        conn.close()
        cookie['sid'] = ''
        cookie['sid']['expires'] = 'Thu, 01 Jan 1970 00:00:00 GMT'
        print cookie
        return 1
    else:
        return None

def redirect(url):
    return "Location: %s" % url

def main():
    global cookie
    cgitb.enable()
    parameters = cgi.FieldStorage()      	#FieldStorage(None, None, [])  now
    string_cookie = os.environ.get('HTTP_COOKIE')
    cookie.load(string_cookie)
    self_username = cookie['sid'].value

    # logout handle
    if parameters.getvalue('action') == 'logout':
        #delete related session here

        #delete related session here
        prompt_logout = "logout successfully."
    else:
        prompt_logout = ""
    # logout handle

    # username, email, full_name, home_suburb, home_latitude, home_longitude
    global flag_update_successfully
    if parameters.getvalue('edit_personal_information'):
        username = parameters.getvalue('username')
        email = parameters.getvalue('email')
        full_name = parameters.getvalue('full_name')
        home_suburb = parameters.getvalue('home_suburb')
        home_latitude = float(parameters.getvalue('home_latitude'))
        home_longitude = float(parameters.getvalue('home_longitude'))
        description = parameters.getvalue('discription')
        conn = sqlite3.connect('users.db')
        conn.execute("update user SET username=?, email=?, full_name=?, home_suburb=?, home_latitude=?, home_longitude=?, description=? WHERE username = ?", (username,email,full_name,home_suburb,home_latitude,home_longitude,description,self_username,))
        conn.commit()
        conn.close()
        flag_update_successfully = 1

    real_change_password(self_username, parameters)
    change_password(self_username, parameters)
    result_change_password(self_username, parameters)
    if delete_account(self_username, parameters):
        print "Location: bitter.cgi"

    print page_header()  #header actually should be processd, it contain home, about, register, and username sign in with password
    dataset_size = "small"
    users_dir = "dataset-%s/users"% dataset_size
    print self_page(prompt_logout, parameters, users_dir)
    print page_trailer(parameters)


def get_self_information():
    global cookie
    string_cookie = os.environ.get('HTTP_COOKIE')
    cookie.load(string_cookie)
    username = cookie['sid'].value
    conn = sqlite3.connect('users.db')
    cursor = conn.execute("SELECT username, password, email, full_name, home_suburb, home_latitude, home_longitude, description from user where username=?", (username,))
    for row in cursor:
        password = row[1]
        email = row[2]
        full_name = row[3]
        home_suburb = row[4]
        home_latitude = str(row[5])
        home_longitude = str(row[6])
        description = row[7]
    return username, password, email, full_name, home_suburb, home_latitude, home_longitude, description


def self_page(prompt_logout, parameters, users_dir):
    global cookie
    global home_latitude_map
    global home_longitude_map
    global flag_update_successfully
    global flag_start_change_password
    global flag_change_password_successfully
    global script_change_password
    prompt_start_change_password = ''
    if flag_start_change_password == 1:
        prompt_start_change_password = "An email has been sent to you, please check it and finish the password change"
    prompt_real_start_change_password = ""
    if flag_real_change_password_status == 1:
        prompt_real_start_change_password = "Please change your password now"
    prompt_change_password_successfully = ""
    if flag_change_password_successfully == 1:
        prompt_change_password_successfully = "Change password successfully"
    prompt_update_successfuly = ""
    if flag_update_successfully == 1:
        prompt_update_successfuly = "updated successfully"
    string_cookie = os.environ.get('HTTP_COOKIE')
    cookie.load(string_cookie)
    username = cookie['sid'].value

    conn = sqlite3.connect('users.db')
    cursor = conn.execute("SELECT username, full_name, home_suburb, home_latitude, home_longitude, description, profile from USER where username=?", (username,))

    attr = ["username", "full_name", "home_suburb", "home_latitude", "home_longitude", "description", "profile"]
    index = 0
    detail_user = ""
    #imageUrl = ""
    for row in cursor:
    #username password email full_name home_suburb home_latitude home_longitude profile description
        detail_user = ""
        index = 0
        for item in row:
            if index == 6:
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
                if index == 0:
                    icon = "glyphicon-user"
                elif index == 1:
                    icon = "glyphicon-star"
                elif index == 2:
                    icon = "glyphicon-home"
                elif index == 3:
                    icon = "glyphicon-zoom-in"
                elif index == 4:
                    icon = "glyphicon-zoom-out"
                elif index == 5:
                    icon = "glyphicon-book"

                detail_user += "<span class=\"glyphicon " + icon + "\"><b> "+attr[index] + " : " + str(item) + "</b></span><br>"
                index += 1
            else:
                index += 1
        detail_user.rstrip("<br>")

    conn.close()

    username, password, email, full_name, home_suburb, home_latitude, home_longitude, description = get_self_information()

    return """
    <div class="jumbotron">
        <div class="container">
            <h5> %s </h5>
            <h5> %s </h5>
            <h5> %s </h5>
            <div class="col-md-4"><img src="%s" /></div>

            <div class="col-md-4"> %s
            <br><br>
            <div class="row">
                <button class="edit btn btn-primary">Edit Information</button>
            </div>
            <br>
            <div class="row">
                <a id="changePassword" class="btn btn-danger" href="?changePassword=true" role="button">Change Password?</a>
                &nbsp;&nbsp;&nbsp;&nbsp;
                <a id="delete" class="btn btn-info" href="?delete=%s" role="button">Delete Account?</a>
             </div>
            <br>


            <p style="color:green;"><small> %s </small></p>
            </div>

            <div class="col-md-4" id="mapholder"></div>
        </div>
    </div>

    <div class="container personal_information" style="display:none;">
        <form method="post" action="" class="form-horizontal">
              <input type='hidden' name='edit_personal_information' value='edit_personal_information'>

              <div class="form-group">
                <label for="username" class="col-sm-2 control-label">Username</label>
                <div class="col-sm-8">
                  <input type="username" class="form-control" name="username" value="%s" id="username" placeholder="Username">
                </div>
              </div>

              <div class="form-group">
                <label for="email" class="col-sm-2 control-label">Email</label>
                <div class="col-sm-8">
                  <input type="email" class="form-control" name="email" value="%s" id="email" placeholder="email">
                </div>
              </div>

              <div class="form-group">
                <label for="full_name" class="col-sm-2 control-label">Full Name</label>
                <div class="col-sm-8">
                  <input type="full_name" class="form-control" name="full_name" value="%s" id="full_name" placeholder="full name">
                </div>
              </div>

              <div class="form-group">
                <label for="home_suburb" class="col-sm-2 control-label">Home Suburb</label>
                <div class="col-sm-8">
                  <input type="home_suburb" class="form-control" name="home_suburb" value="%s" id="home_suburb" placeholder="home suburb">
                </div>
              </div>

              <div class="form-group">
                <label for="home_latitude" class="col-sm-2 control-label">Home Latitude</label>
                <div class="col-sm-8">
                  <input type="home_latitude" class="form-control" name="home_latitude" value="%s" id="home_latitude" placeholder="home latitude">
                </div>
              </div>

              <div class="form-group">
                <label for="home_longitude" class="col-sm-2 control-label">Home Longitude</label>
                <div class="col-sm-8">
                  <input type="home_longitude" class="form-control" name="home_longitude" value="%s" id="home_longitude" placeholder="home_longitude">
                </div>
              </div>

              <div class="form-group">
                <label for="discription" class="col-sm-2 control-label">Description</label>
                <div class="col-sm-8">
                  <input type="discription" class="form-control" name="discription" value="%s" id="discription" placeholder="discription(eg:interest......)">
                </div>
              </div>

              <div class="form-group">
                <div class="col-sm-8 col-sm-offset-2">
                   <button type="submit" class="btn btn-primary">Confirm Information</button>
                </div>
              </div>
             <hr>
        </form>
    </div>
    <br>

    <script type="text/javascript">
        $(document).ready(function(){
          $(".edit").click(function(){
               $(this).parent().parent().parent().parent().next(".personal_information").toggle("fast");
          });
        });
    </script>
    %s
    """ % (prompt_start_change_password, prompt_real_start_change_password, prompt_change_password_successfully, imageUrl, detail_user, username, prompt_update_successfuly, username, email, full_name, home_suburb, home_latitude, home_longitude, description, script_change_password)


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
<link rel='stylesheet' href='stylesheets/profile.css' />
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
              <input type="text" class="form-control" placeholder="Search User Or Bleat">
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
    flag_update_successfully = 0
    flag_start_change_password = 0
    flag_real_change_password_status = 0
    flag_change_password_successfully = 0
    cookie = Cookie.SimpleCookie()
    debug = 1
    flag_logout = 0
    home_latitude_map = 0.0
    home_longitude_map = 0.0
    script_change_password = ""
    main()

