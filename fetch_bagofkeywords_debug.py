from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker,scoped_session
from sqlalchemy.pool import NullPool
from my_declarative_base import Images, BagOfKeywords,Keywords,ImagesKeywords,ImagesEthnicity  # Replace 'your_module' with the actual module where your SQLAlchemy models are defined
from mp_db_io import DataIO
import pickle
import numpy as np
from pick import pick
import threading
import queue

io = DataIO()
db = io.db
io.db["name"] = "stock"

# Create a database engine
engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}".format(host=db['host'], db=db['name'], user=db['user'], pw=db['pass']), poolclass=NullPool)

# Create a session
session = scoped_session(sessionmaker(bind=engine))


title = 'Please choose your operation: '
options = ['Create table', 'Fetch keywords list', 'Fetch ethnicity list']
option, index = pick(options, title)

LIMIT= 1000
# Initialize the counter
counter = 0

# Number of threads
num_threads = io.NUMBER_OF_PROCESSES

def create_table(row, lock, session):
    try:
        image_id, description, gender_id, age_id, location_id = row
        
        print("Inside create_table with param: ", row)

        print("Trying to acquire lock")

        with lock:
            print("Acquired lock")            
            # Create a BagOfKeywords object
            bag_of_keywords = BagOfKeywords(
                image_id=image_id,
                description=description,
                gender_id=gender_id,
                age_id=age_id,
                location_id=location_id,
                keyword_list=None,  # Set this to None or your desired value
                ethnicity_list=None  # Set this to None or your desired value
            )

            # Print a message to confirm the update
            print(f"Created BagOfKeywords object: {bag_of_keywords}")

            if bag_of_keywords is not None:
                print("Adding BagOfKeywords to session")
                session.add(bag_of_keywords)
                print("Added BagOfKeywords to session")
                
        print("Releasing lock")
        print("Finished processing param: ", row)
    except Exception as e:
        print("Exception in create_table: ", e)

    try:    
        with lock:
            # Increment the counter using the lock to ensure thread safety
            global counter
            counter += 1
            print("Incremented counter")
            print("Releasing lock")
        print("Finished processing param: ", row)
    except Exception as e:
        print("Exception in create_table: ", e)


def fetch_keywords(target_image_id, lock,session):
    #global session
    # Build a select query to retrieve keyword_ids for the specified image_id
    select_keyword_ids_query = (
        select(ImagesKeywords.keyword_id)
        .filter(ImagesKeywords.image_id == target_image_id)
    )

    # Execute the query and fetch the result as a list of keyword_ids
    result = session.execute(select_keyword_ids_query).fetchall()
    keyword_ids = [row.keyword_id for row in result]

    # Build a select query to retrieve keywords for the specified keyword_ids
    select_keywords_query = (
        select(Keywords.keyword_text)
        .filter(Keywords.keyword_id.in_(keyword_ids))
        .order_by(Keywords.keyword_id)
    )

    # Execute the query and fetch the results as a list of keyword_text
    result = session.execute(select_keywords_query).fetchall()
    keyword_list = [row.keyword_text for row in result]
    # Pickle the keyword_list
    keyword_list_pickle = pickle.dumps(keyword_list)

    # Update the BagOfKeywords entry with the corresponding image_id
    BOK_keywords_entry = (
        session.query(BagOfKeywords)
        .filter(BagOfKeywords.image_id == target_image_id)
        .first()
    )

    if BOK_keywords_entry:
        BOK_keywords_entry.keyword_list = keyword_list_pickle
        #session.commit()
        print(f"Keyword list for image_id {target_image_id} updated successfully.")
    else:
        print(f"Keywords entry for image_id {target_image_id} not found.")
        
    with lock:
        # Increment the counter using the lock to ensure thread safety
        global counter
        counter += 1

    return

def fetch_ethnicity(target_image_id, lock, session):
    select_ethnicity_ids_query = (
        select(ImagesEthnicity.ethnicity_id)
        .filter(ImagesEthnicity.image_id == target_image_id)
    )

    result = session.execute(select_ethnicity_ids_query).fetchall()
    ethnicity_list = [row.ethnicity_id for row in result]

    ethnicity_list_pickle = pickle.dumps(ethnicity_list)

    # Update the BagOfKeywords entry with the corresponding image_id
    BOK_ethnicity_entry = (
        session.query(BagOfKeywords)
        .filter(BagOfKeywords.image_id == target_image_id)
        .first()
    )

    if BOK_ethnicity_entry:
        BOK_ethnicity_entry.ethnicity_list = ethnicity_list_pickle
        #session.commit()
        print(f"Ethnicity list for image_id {target_image_id} updated successfully.")
    else:
        print(f"ethnicity entry for image_id {target_image_id} not found.")
    
    with lock:
        # Increment the counter using the lock to ensure thread safety
        global counter
        counter += 1

    return



#######MULTI THREADING##################
# Create a lock for thread synchronization
lock = threading.Lock()
threads_completed = threading.Event()



# Create a queue for distributing work among threads
work_queue = queue.Queue()

if index == 0:
    function=create_table
    ################# CREATE TABLE ###########
    select_query = select(Images.image_id, Images.description, Images.gender_id, Images.age_id, Images.location_id).select_from(Images).outerjoin(BagOfKeywords, Images.image_id == BagOfKeywords.image_id).filter(BagOfKeywords.image_id == None).limit(LIMIT)
    result = session.execute(select_query).fetchall()
    for row in result:
        work_queue.put(row)

elif index == 1:
    function=fetch_keywords
    ################FETCHING KEYWORDS####################################
    distinct_image_ids_query = select(BagOfKeywords.image_id.distinct()).filter(BagOfKeywords.keyword_list == None).limit(LIMIT)
    distinct_image_ids = [row[0] for row in session.execute(distinct_image_ids_query).fetchall()]
    for target_image_id in distinct_image_ids:
        work_queue.put(target_image_id)
        
elif index == 2:
    function=fetch_ethnicity
    #################FETCHING ETHNICITY####################################
    distinct_image_ids_query = select(BagOfKeywords.image_id.distinct()).filter(BagOfKeywords.ethnicity_list == None).limit(LIMIT)
    distinct_image_ids = [row[0] for row in session.execute(distinct_image_ids_query).fetchall()]
    for target_image_id in distinct_image_ids:
        work_queue.put(target_image_id)        

def threaded_fetching():
    # Create a new session for this thread
    session = scoped_session(sessionmaker(bind=engine))

    print("Size of work_queue at start: ", work_queue.qsize())

    while not work_queue.empty():
        try:
            param = work_queue.get()
            print("Number of objects in session.new before function call: ", len(session.new))
            print("Number of objects in session.identity_map before function call: ", len(list(session.identity_map)))
            with lock:
                function(param, lock, session)
                print("Number of objects in session.new after function call: ", len(session.new))
                print("Number of objects in session.identity_map after function call: ", len(list(session.identity_map)))
            work_queue.task_done()
        except Exception as e:
            print("Exception in threaded_fetching: ", e)

    # Close the session
    session.remove()


    a    
def threaded_processing():
    thread_list = []
    for _ in range(num_threads):
        thread = threading.Thread(target=threaded_fetching)
        thread_list.append(thread)
        thread.start()
    # Wait for all threads to complete
    for thread in thread_list:
        thread.join()
    # Set the event to signal that threads are completed
    threads_completed.set()

threaded_processing()
# Commit the changes to the database
threads_completed.wait()

# Print the number of objects in the session
print("Number of objects in the session.new before commit: ", len(session.new))

# Print the number of objects in the session
print("Number of objects in the session.identity_map before commit: ", len(list(session.identity_map)))

# Commit the changes to the database
session.commit()
print("committed session")

# Close the session
session.close()
print("closed session")