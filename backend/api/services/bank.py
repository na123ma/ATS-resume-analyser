"""Original fixed assessment questions. Change BANK_VERSION when editing them."""
import copy
import secrets
from ..db import uid

BANK_VERSION = 'foundations-v1'
TECHNOLOGIES = ['Python', 'JavaScript', 'React', 'Django', 'SQL', 'Java']
# Correct answer is first here; every delivered attempt shuffles choices server-side.
ROWS = {
'Python': [
('Which Python collection is mutable?', 'list|tuple|str|frozenset', 'A list can be modified after creation; the other listed types are immutable.'),
('What does len({1, 1, 2}) return?', '2|3|1|0', 'Sets contain unique values, so this set contains 1 and 2.'),
('What does a Python generator return when called?', 'A generator iterator|A complete list|A string|A new thread', 'Calling a generator function creates an iterator. Its body advances when iterated.'),
('Which syntax catches a ValueError?', 'except ValueError:|catch ValueError:|handle ValueError:|error ValueError:', 'Python handles exceptions with try and except clauses.'),
('What does [x * 2 for x in range(3)] produce?', '[0, 2, 4]|[2, 4, 6]|[0, 1, 2]|[0, 2, 4, 6]', 'range(3) produces 0, 1, 2 and each value is multiplied by 2.'),
('Why is a mutable default function argument risky?', 'It is reused across calls|It is always copied|It makes the function recursive|It disables exceptions', 'Default argument expressions are evaluated at function definition time.'),
('What is the average lookup complexity of a Python dictionary?', 'O(1)|O(n)|O(n log n)|O(n squared)', 'Hash table lookup is average constant time, although collisions can worsen it.'),
('What does the with statement help manage?', 'Resource cleanup|Integer overflow|Package installation|Static typing', 'Context managers perform enter and exit actions, such as closing a file.'),
('Which operator tests object identity?', 'is|==|in|!=', 'is compares identity; == compares values using equality semantics.'),
('What does a decorator typically do?', 'Wrap or transform a function or class|Delete a module|Always start a thread|Convert every value to text', 'A decorator receives an object and returns the replacement bound to its name.'),
],
'JavaScript': [
('What does strict equality (===) avoid?', 'Implicit type coercion|All object comparisons|Boolean results|Checking primitive values', 'Strict equality compares values without converting between different types.'),
('Which keyword declares a block-scoped reassignable binding?', 'let|var|static|def', 'let is block-scoped and permits reassignment; const does not permit rebinding.'),
('What does an async function always return?', 'A Promise|A plain string|An array|An event listener', 'An async function wraps its return value in a Promise.'),
('What is a closure?', 'A function retaining access to its lexical environment|A closed browser tab|A class without methods|An expired Promise', 'Closures allow functions to access bindings from the scope where they were created.'),
('Which array method returns a new array of transformed elements?', 'map|forEach|push|pop', 'map applies a callback and collects its return values in a new array.'),
('What does JSON.parse do?', 'Converts JSON text into a JavaScript value|Runs JavaScript source|Encrypts an object|Sends an HTTP request', 'JSON.parse parses JSON, not arbitrary JavaScript code.'),
('When is a Promise then callback normally run?', 'As a microtask after the current synchronous stack|Before the current expression completes|Only after one minute|On its own operating-system thread', 'Promise reactions run in the microtask queue after synchronous work yields.'),
('Which syntax creates a shallow copy of an array a?', '[...a]|a.cloneDeep()|copy(a, deep)|a === []', 'Array spread copies the top-level sequence but nested objects remain shared.'),
('What does event.preventDefault() do?', 'Cancels a cancelable default browser action|Stops all network traffic|Always stops event propagation|Deletes the event target', 'Preventing the default action is separate from stopping event propagation.'),
('What should you check after fetch resolves for an HTTP 404?', 'response.ok or response.status|Whether fetch returned undefined|Whether a catch always ran|Whether JSON is encrypted', 'fetch usually resolves for HTTP errors, so inspect the HTTP status yourself.'),
],
'React': [
('What should a React component return?', 'A renderable React node|A SQL connection|Only a string|A CSS file path', 'Components describe renderable UI with React nodes, commonly JSX.'),
('Which hook stores local component state?', 'useState|useRoute|useStyle|useQuerySQL', 'useState gives a component a state value and a setter.'),
('Why do list items need stable keys?', 'To help React track item identity|To encrypt the list|To sort the array automatically|To avoid using props', 'Stable keys help reconciliation preserve the correct component identity.'),
('How should you update an array held in React state?', 'Create a new array and use its setter|Mutate it and skip the setter|Change the DOM directly|Assign to a prop', 'Treat state as immutable and pass a new reference to the setter.'),
('What is a controlled input?', 'An input whose value is driven by React state|An input that cannot be edited|An input outside the DOM|A server-only input', 'A controlled input receives its value and updates it through an event handler.'),
('Where may hooks normally be called?', 'At the top level of components or custom hooks|Inside any conditional branch|Only inside click handlers|Inside ordinary class methods', 'Stable hook call order is required; do not call hooks conditionally.'),
('What is an effect cleanup useful for?', 'Removing subscriptions or timers|Changing every prop|Skipping all renders|Writing JSX into CSS', 'Cleanup releases external resources and avoids obsolete subscriptions.'),
('How can state be shared between sibling components?', 'Lift it to a common parent|Copy it into global HTML|Mutate one sibling from the other|Use duplicate keys', 'A common owner can pass state and callbacks to both siblings.'),
('What does useRef preserve across renders?', 'A mutable reference that does not itself trigger rendering|An automatic HTTP response|A new component class each render|Only immutable numbers', 'The ref object persists and changing current does not trigger a render.'),
('Which update safely increments based on previous state?', 'setCount(c => c + 1)|count++|props.count = count + 1|setCount = count + 1', 'A functional state update receives the pending previous state.'),
],
'Django': [
('Which Django layer maps URL paths to view functions?', 'URLconf|Template loader|Password hasher|Migration recorder', 'URL patterns route a matching request path to its view.'),
('What does a Django migration describe?', 'A database schema change|A browser animation|A password value|A CSS dependency', 'Migrations track and apply changes to the database schema for ORM models.'),
('Why should you use Django password hashing helpers?', 'To store salted adaptive password hashes|To store plaintext passwords|To make passwords reversible|To place passwords in URLs', 'Adaptive salted hashes make offline password guessing more expensive.'),
('What is CSRF protection designed to prevent?', 'Unwanted authenticated cross-site requests|Every possible SQL query|All phishing email|Reading public pages', 'CSRF protections stop another site from silently triggering state changes using a user session.'),
('Which ORM method retrieves exactly one matching object?', 'get|filter|all|order_by', 'get expects one result and raises an exception if there are zero or multiple results.'),
('What does select_related primarily optimize?', 'Fetching related foreign-key or one-to-one objects|CSS delivery|Password hashing|Email formatting', 'select_related uses joins to avoid additional queries for suitable relations.'),
('Why validate data on the server?', 'Clients can bypass browser validation|Browsers never support forms|Validation is only for styling|It guarantees no network failures', 'Treat client requests as untrusted and validate on the server.'),
('What does Django template autoescaping reduce?', 'HTML injection and many XSS risks|Database storage size|All CSRF risks|Server CPU temperature', 'Autoescaping escapes HTML special characters; unsafe contexts still need care.'),
('What should DEBUG normally be in production?', 'False|True|The database password|An empty list', 'Production must not expose development tracebacks and sensitive configuration details.'),
('What is middleware used for?', 'Cross-cutting request and response processing|Only creating database indexes|Only rendering images|Changing Python syntax', 'Middleware can implement behavior such as security headers and request processing.'),
],
'SQL': [
('Which clause filters rows before grouping?', 'WHERE|HAVING|ORDER BY|LIMIT', 'WHERE filters input rows; HAVING filters grouped results.'),
('Which join preserves all rows from the left table?', 'LEFT JOIN|INNER JOIN|CROSS JOIN only|SELF JOIN only', 'LEFT JOIN keeps unmatched left rows and fills right-side columns with NULL.'),
('What does COUNT(*) count?', 'Rows including rows with NULL values|Only non-NULL values in one column|Only distinct rows|Only primary keys', 'COUNT(*) counts rows; COUNT(column) ignores NULL in that column.'),
('How do you correctly test whether a value is NULL?', 'IS NULL|= NULL|== NULL|LIKE NULL', 'NULL uses three-valued logic, so use IS NULL rather than ordinary equality.'),
('What does a primary key guarantee?', 'Unique non-NULL row identifiers|Rows are always sorted|Every column is numeric|No foreign keys are allowed', 'A primary key uniquely identifies a row and does not allow NULL.'),
('What can an index trade for faster reads?', 'Additional storage and write cost|Guaranteed zero storage|Removal of all locks|Automatic data encryption', 'Indexes consume space and must be maintained when indexed data changes.'),
('Which command commits a transaction?', 'COMMIT|SAVE|PERSIST ALL|FINISH TABLE', 'COMMIT makes a successful transaction durable according to database guarantees.'),
('How do parameterized queries help security?', 'Separate SQL structure from supplied values|Make all users administrators|Disable authentication|Automatically hide all data', 'Parameters prevent values being interpreted as SQL syntax.'),
('What does GROUP BY do?', 'Groups rows for aggregate calculations|Deletes duplicate tables|Sorts every column descending|Starts a transaction', 'GROUP BY combines rows with matching grouping keys for aggregates.'),
('Which query reliably returns the highest salary first?', 'SELECT salary FROM employees ORDER BY salary DESC|SELECT salary FROM employees|SELECT salary FROM employees LIMIT 1|SELECT salary FROM employees GROUP BY salary', 'Only an explicit appropriate ORDER BY guarantees the requested ordering.'),
],
'Java': [
('Which Java type represents a true/false value?', 'boolean|bool|bitstring|truth', 'Java uses the primitive boolean type for true and false.'),
('Which method is the usual Java application entry point?', 'public static void main(String[] args)|public run()|start application()|private void entry()', 'The conventional Java launcher invokes a public static main method with String[] arguments.'),
('How do you normally compare String contents?', 'equals()|==|===|compareIdentity()', 'equals compares String contents; == checks reference identity.'),
('What does an interface primarily define?', 'A contract for implementing types|An operating-system process|Only a database table|A memory address', 'Interfaces define capabilities that implementing classes provide.'),
('Which collection stores unique elements?', 'Set|List|ArrayList only|StringBuilder', 'Set does not contain duplicate elements according to its equality semantics.'),
('What does final on a variable prevent?', 'Reassigning the variable|All mutation of referenced objects|Reading the variable|Garbage collection', 'A final reference cannot be reassigned, but the referenced object may still be mutable.'),
('What is method overloading?', 'Methods with the same name and different parameter lists|Changing only a return type|Deleting inherited methods|Making all methods static', 'Overloaded methods differ in their parameter lists.'),
('What does try-with-resources manage?', 'Automatic closing of AutoCloseable resources|Automatic class inheritance|Starting all threads|Disabling exceptions', 'Resources implementing AutoCloseable are closed when the block exits.'),
('Why use a synchronized block?', 'To coordinate access using a shared monitor|To make every method faster|To bypass thread safety|To copy a class', 'Threads locking the same monitor can coordinate mutually exclusive access.'),
('Which map is designed for concurrent access?', 'ConcurrentHashMap|An unsynchronized HashMap always|TreeMap always|ArrayList', 'ConcurrentHashMap supports concurrent access; plain HashMap needs external coordination.'),
],
}


def questions(technology, shuffle=True):
    result = []
    for i, (question, answers, explanation) in enumerate(ROWS[technology]):
        options = answers.split('|')
        correct_text = options[0]
        if shuffle:
            secrets.SystemRandom().shuffle(options)
        result.append({'id': uid(), 'question': question, 'options': options,
                       'correct': options.index(correct_text), 'explanation': explanation})
    if shuffle:
        secrets.SystemRandom().shuffle(result)
    return result


def interview_questions(technology, difficulty):
    base = [
        f'Explain a core concept in {technology} and show a small example of how you used it.',
        f'Describe how you would debug an unexpected result in a {technology} project.',
        f'How would you test a feature written with {technology}? Give specific test cases.',
        f'Describe a performance or security problem in {technology} and how you would approach it.',
        f'Walk me through a {technology} project decision, its trade-offs and what you learned.',
    ]
    if difficulty == 'medium':
        base[0] = f'Explain how you would structure a maintainable {technology} application and justify your choices.'
    if difficulty == 'hard':
        base[0] = f'How would you diagnose a concurrency or scalability failure in a production {technology} application?'
        base[3] = f'Compare two architecture choices for a high-load {technology} service, including failure modes and observability.'
    return base
