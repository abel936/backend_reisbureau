
def get_users():
  """
  Return all users from the table: Users in a dictionary with ID and first name
  """
  myconn, mycursor = get_cursor()
  mycursor.execute("""SELECT PersonID, FirstName, LastName FROM users""")
  users = mycursor.fetchall()
  users = [{"PersonID": user[0], "FullName": user[1] + " " + user[2]} for user in users]

  close_conn(myconn, mycursor)

  return users

def start():
    """This function returns the output on the /abel page"""
    return