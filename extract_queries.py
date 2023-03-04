#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Author : DASARI B BHARADWAJ

This Python script defines a set of functions and classes that generate queries based on Boolean expressions and a
query type. The script defines two dictionaries BASE_QUERIES and END_QUERIES to store base and end queries for different
query types (SQL, MONGODB, and ORM). It also defines a Node class to represent a node in an expression tree, as well as
several functions to generate queries based on a given expression tree, including inorder, inorder_orm, and preorder.

The create_query function takes a root node and a query type as inputs and generates a final query by calling the
corresponding function to generate the query for the given query type. The generate_node function creates a node
representing an operator in the expression, and the create_exp_tree function creates an expression tree for the given
expression. The generate_query function generates a query based on a Boolean expression and a query type.

This script can be used to generate queries for different database management systems based on Boolean expressions,
allowing for more flexible querying of data.

Example :
----------
        exp = (Java AND Spring) OR (Python AND Django)

        exp_tree would look like :
                                     (OR)               # root node
                                /            \
                           (AND)              (AND)     # LEVEL 1 Operators
                          /     \            /     \
                      (JAVA) (Spring)   (Python) (Django)  # Leaf nodes

        Now the tree can be traversed inorder, preorder or postorder depending on the query type syntax.

Assumptions :
--------------
    -> The search for sql queries is made case-sensitive, If otherwise lower() can be used to achieve that.
    -> For MongoDB query type, Only query dict will be returned which can work with mongoDB compass.

Expected inputs :
-----------------
    command : Boolean expressions with usage of brackets and keywords 'OR' and 'AND'
    query_type : Currently only three types of query types are allowed:
              -> SQL : For sql queries
              -> MONGODB : For mongodb query dictionary
              -> ORM : For ORM queryset
              -> ElasticSearch : For Elastic DSL query
"""


# Define base queries for different query types
BASE_QUERIES = {
    'SQL': "SELECT * FROM Resume WHERE ",
    'MONGODB': "{",
    'ORM': "",
    'ELASTICSEARCH': """ "query": """
}

# Define end queries for different query types
END_QUERIES = {
    'SQL': '',
    'MONGODB': '}',
    "ORM": '',
    'ELASTICSEARCH': ""
}


class Node:
    """ A class to represent a node in an expression tree. """

    def __init__(self, value):
        """
        Initializes a Node object with the given value.

        Args:
            value (str): The value of the node.
        """
        self.value = value
        self.left = None  # Left child
        self.right = None  # Right child


def inorder(node: Node):
    """
    Traverses the expression tree in-order and generates the corresponding SQL query.

    Args:
        node (Node): The root node of the expression tree.

    Returns:
        str: The SQL query generated from the expression tree.
    """
    if node and node.left:
        return f"({inorder(node.left)} {node.value} {inorder(node.right)})"
    elif node:
        return f" text like '%{node.value}%'"


def inorder_orm(node: Node):
    """
    Traverses the expression tree in-order and generates the corresponding ORM query.

    Args:
        node (Node): The root node of the expression tree.

    Returns:
        str: The ORM query generated from the expression tree.
    """
    if node and node.left:
        return f"Q({inorder_orm(node.left)}) {node.value} Q({inorder_orm(node.right)})"
    elif node:
        return f"text__icontains='{node.value}'"


def preorder(node: Node):
    """
    Traverses the expression tree pre-order and generates the corresponding MongoDB query.

    Args:
        node (Node): The root node of the expression tree.

    Returns:
        str: The MongoDB query generated from the expression tree.
    """
    if node and node.left:
        return f""" ${node.value} : [{preorder(node.left)}, {preorder(node.right)}]"""
    elif node:
        return """{"text" : /.*""" + node.value + """.*/i}"""


def preorder_elasticsearch(node: Node):
    """
    Traverses the expression tree pre-order and generates the corresponding ElasticSearch query.

    Args:
        node (Node): The root node of the expression tree.

    Returns:
        str: The MongoDB query generated from the expression tree.
    """
    if node and node.left:
        return ' { "bool" : {' + f""" {node.value} : [{preorder_elasticsearch(node.left)}, {preorder_elasticsearch(node.right)}]""" + "} }"
    elif node:
        return """{"match" : { "text" : {""" + '"' + node.value + '"' + """} } """


def create_query(root: Node, query_type: str) -> str:
    """
    Generates the final query by calling the corresponding function to generate the query for the given query type.

    Args:
        root (Node): The root node of the expression tree.
        query_type (str): The type of query to be generated.

    Returns:
        str: The final query generated.
    """

    temp_query = ''

    if query_type == 'ORM':
        temp_query = inorder_orm(root)
        temp_query = temp_query.replace('&', ',')

    elif query_type == 'ELASTICSEARCH':
        temp_query = preorder_elasticsearch(root)
        temp_query = temp_query.replace('|', '"SHOULD"')
        temp_query = temp_query.replace('&', '"MUST"')

    elif query_type == 'SQL':
        temp_query = inorder(root)[1:-1]
        temp_query = temp_query.replace('|', 'OR')
        temp_query = temp_query.replace('&', 'AND')

    elif query_type == 'MONGODB':
        temp_query = preorder(root)
        temp_query = temp_query.replace('|', 'OR')
        temp_query = temp_query.replace('&', 'AND')

    final_query = BASE_QUERIES[query_type] + temp_query + END_QUERIES[query_type]
    return final_query


def generate_node(exp: str) -> Node:
    """Create a node representing an operator in the expression.

    Args:
        exp (str): A string representing the expression containing the operator.

    Returns:
        Node: A node representing the operator.
    """

    idx = None

    if '|' in exp:
        idx = exp.index('|')
    elif '&' in exp:
        idx = exp.index('&')

    opnode = Node(exp[idx].strip())
    lnode = Node(exp[:idx].strip())
    rnode = Node(exp[idx + 1:].strip())
    opnode.left = lnode
    opnode.right = rnode

    return opnode


def create_exp_tree(exp: str) -> Node:
    """
    Create an expression tree for the given expression.

    Args:
        exp (str): A string representing the expression.

    Returns:
        Node: The root node of the expression tree.
    """

    node = None

    # If the expression contains only one variable, create a node for that variable and return it
    if '|' not in exp and '&' not in exp:
        node = Node(exp)
        return node

    # If the expression is surrounded by parentheses, remove them and create the expression tree for the contents
    if exp.count('(') < 1 and exp[-1:] == ')':
        exp = exp.replace('(', '')
        exp = exp.replace(')', '')
        return generate_node(exp)

    # If the expression contains multiple variables or operators, create the expression tree recursively
    lopen = 0

    flag = 0

    for i in range(len(exp)):
        if exp[i] == '(':
            lopen += 1
        elif exp[i] == ')':
            lopen -= 1
        elif exp[i] in ['|', '&'] and lopen == 0:
            flag = 1
            node = Node(exp[i])
            lnode = create_exp_tree(exp[:i].strip())
            rnode = create_exp_tree(exp[i + 1:].strip())
            node.left = lnode
            node.right = rnode

    if flag == 1:
        return node
    else:  # After brackets are close no operator exists to the right
        return create_exp_tree(exp[1:-1])


def generate_query(exp: str, query_type: str) -> str:
    """
    Generates a query based on a Boolean expression and a query type.

    Args:
        exp (str): A string representing a Boolean expression.
        query_type (str): A string representing the type of query to generate.
                          Currently only three types of query types are allowed:
                          SQL : For sql queries
                          MONGODB : For mongodb query dictionary
                          ORM : For ORM queryset
                          ElasticSearch : For Elastic DSL query

    Returns:
        str: A string representing the generated query.
    """

    query_type = query_type.upper()
    if query_type not in BASE_QUERIES.keys():
        return "Invalid query type request. SQL, MONGODB, and ORM are only currently accepted query types"

    value_dict = {
        '(': ' ( ',
        ')': ' ) ',
        ' OR ': '|',
        ' or ': '|',
        ' AND ': '&',
        ' and ': '&',
        '"': ''
    }

    # Replace expression with single characters
    for key, value in value_dict.items():
        exp = exp.replace(key, value)

    # create expression tree :
    root = create_exp_tree(exp)

    # Get query
    raw_query = create_query(root, query_type)
    print(raw_query)
    return raw_query


###########################################** END OF CODE** ############################################################

# Input variables
command = """(Java AND Spring) OR (Python AND Django) """  # Expression
query_type_req = 'SQL'  # query type

# To generate query from exp
generate_query(command, query_type_req)

########################################################################################################################
