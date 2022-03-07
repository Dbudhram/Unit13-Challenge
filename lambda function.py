{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "54ad785a",
   "metadata": {},
   "outputs": [],
   "source": [
    "### Required Libraries ###\n",
    "from datetime import datetime\n",
    "from dateutil.relativedelta import relativedelta\n",
    "\n",
    "### Functionality Helper Functions ###\n",
    "def parse_int(n):\n",
    "    \"\"\"\n",
    "    Securely converts a non-integer value to integer.\n",
    "    \"\"\"\n",
    "    try:\n",
    "        return int(n)\n",
    "    except ValueError:\n",
    "        return float(\"nan\")\n",
    "\n",
    "\n",
    "def build_validation_result(is_valid, violated_slot, message_content):\n",
    "    \"\"\"\n",
    "    Define a result message structured as Lex response.\n",
    "    \"\"\"\n",
    "    if message_content is None:\n",
    "        return {\"isValid\": is_valid, \"violatedSlot\": violated_slot}\n",
    "\n",
    "    return {\n",
    "        \"isValid\": is_valid,\n",
    "        \"violatedSlot\": violated_slot,\n",
    "        \"message\": {\"contentType\": \"PlainText\", \"content\": message_content},\n",
    "    }\n",
    "\n",
    "\n",
    "def get_investment_recommendation(risk_level):\n",
    "    \"\"\"\n",
    "    Returns an initial investment recommendation based on the risk profile.\n",
    "    \"\"\"\n",
    "    risk_levels = {\n",
    "        \"none\": \"100% bonds (AGG), 0% equities (SPY)\",\n",
    "        \"very low\": \"80% bonds (AGG), 20% equities (SPY)\",\n",
    "        \"low\": \"60% bonds (AGG), 40% equities (SPY)\",\n",
    "        \"medium\": \"40% bonds (AGG), 60% equities (SPY)\",\n",
    "        \"high\": \"20% bonds (AGG), 80% equities (SPY)\",\n",
    "        \"very high\": \"0% bonds (AGG), 100% equities (SPY)\",\n",
    "    }\n",
    "\n",
    "    return risk_levels[risk_level.lower()]\n",
    "\n",
    "\n",
    "def validate_data(age, investment_amount, intent_request):\n",
    "    \"\"\"\n",
    "    Validates the data provided by the user.\n",
    "    \"\"\"\n",
    "\n",
    "    # Validate the retirement age based on the user's current age.\n",
    "    # An retirement age of 65 years is considered by default.\n",
    "    if age is not None:\n",
    "        age = parse_int(\n",
    "            age\n",
    "        )  # Since parameters are strings it's important to cast values\n",
    "        if age < 0:\n",
    "            return build_validation_result(\n",
    "                False,\n",
    "                \"age\",\n",
    "                \"Cannot compute for the unborn, please provide an age of 0 or greater\",\n",
    "            )\n",
    "        elif age >= 65:\n",
    "            return build_validation_result(\n",
    "                False,\n",
    "                \"age\",\n",
    "                \"Cannot provide portfolio recommendation for your age, \"\n",
    "                \" please provide an age between 0 and 65\",\n",
    "            )\n",
    "\n",
    "    # Validate the investment amount, it should be >= 5000\n",
    "    if investment_amount is not None:\n",
    "        investment_amount = parse_int(investment_amount)\n",
    "        if investment_amount < 5000:\n",
    "            return build_validation_result(\n",
    "                False,\n",
    "                \"investmentAmount\",\n",
    "                \"The investment amount selected cannot be used, \"\n",
    "                \" please provide amount of $5,000 or greater\",\n",
    "            )\n",
    "\n",
    "    return build_validation_result(True, None, None)\n",
    "\n",
    "\n",
    "### Dialog Actions Helper Functions ###\n",
    "def get_slots(intent_request):\n",
    "    \"\"\"\n",
    "    Fetch all the slots and their values from the current intent.\n",
    "    \"\"\"\n",
    "    return intent_request[\"currentIntent\"][\"slots\"]\n",
    "\n",
    "\n",
    "def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):\n",
    "    \"\"\"\n",
    "    Defines an elicit slot type response.\n",
    "    \"\"\"\n",
    "\n",
    "    return {\n",
    "        \"sessionAttributes\": session_attributes,\n",
    "        \"dialogAction\": {\n",
    "            \"type\": \"ElicitSlot\",\n",
    "            \"intentName\": intent_name,\n",
    "            \"slots\": slots,\n",
    "            \"slotToElicit\": slot_to_elicit,\n",
    "            \"message\": message,\n",
    "        },\n",
    "    }\n",
    "\n",
    "\n",
    "def delegate(session_attributes, slots):\n",
    "    \"\"\"\n",
    "    Defines a delegate slot type response.\n",
    "    \"\"\"\n",
    "\n",
    "    return {\n",
    "        \"sessionAttributes\": session_attributes,\n",
    "        \"dialogAction\": {\"type\": \"Delegate\", \"slots\": slots},\n",
    "    }\n",
    "\n",
    "\n",
    "def close(session_attributes, fulfillment_state, message):\n",
    "    \"\"\"\n",
    "    Defines a close slot type response.\n",
    "    \"\"\"\n",
    "\n",
    "    response = {\n",
    "        \"sessionAttributes\": session_attributes,\n",
    "        \"dialogAction\": {\n",
    "            \"type\": \"Close\",\n",
    "            \"fulfillmentState\": fulfillment_state,\n",
    "            \"message\": message,\n",
    "        },\n",
    "    }\n",
    "\n",
    "    return response\n",
    "\n",
    "\n",
    "### Intents Handlers ###\n",
    "def recommend_portfolio(intent_request):\n",
    "    \"\"\"\n",
    "    Performs dialog management and fulfillment for recommending a portfolio.\n",
    "    \"\"\"\n",
    "\n",
    "    first_name = get_slots(intent_request)[\"firstName\"]\n",
    "    age = get_slots(intent_request)[\"age\"]\n",
    "    investment_amount = get_slots(intent_request)[\"investmentAmount\"]\n",
    "    risk_level = get_slots(intent_request)[\"riskLevel\"]\n",
    "    source = intent_request[\"invocationSource\"]\n",
    "\n",
    "    if source == \"DialogCodeHook\":\n",
    "        # Perform basic validation on the supplied input slots.\n",
    "        # Use the elicitSlot dialog action to re-prompt\n",
    "        # for the first violation detected.\n",
    "        slots = get_slots(intent_request)\n",
    "\n",
    "        validation_result = validate_data(age, investment_amount, intent_request)\n",
    "        if not validation_result[\"isValid\"]:\n",
    "            slots[validation_result[\"violatedSlot\"]] = None  # Cleans invalid slot\n",
    "\n",
    "            # Returns an elicitSlot dialog to request new data for the invalid slot\n",
    "            return elicit_slot(\n",
    "                intent_request[\"sessionAttributes\"],\n",
    "                intent_request[\"currentIntent\"][\"name\"],\n",
    "                slots,\n",
    "                validation_result[\"violatedSlot\"],\n",
    "                validation_result[\"message\"],\n",
    "            )\n",
    "\n",
    "        # Fetch current session attibutes\n",
    "        output_session_attributes = intent_request[\"sessionAttributes\"]\n",
    "\n",
    "        return delegate(output_session_attributes, get_slots(intent_request))\n",
    "\n",
    "    # Get the initial investment recommendation\n",
    "    initial_recommendation = get_investment_recommendation(risk_level)\n",
    "\n",
    "    # Return a message with the initial recommendation based on the risk level.\n",
    "    return close(\n",
    "        intent_request[\"sessionAttributes\"],\n",
    "        \"Fulfilled\",\n",
    "        {\n",
    "            \"contentType\": \"PlainText\",\n",
    "            \"content\": \"\"\"{} thank you for your information;\n",
    "            based on the risk level you defined, my recommendation is to choose an investment portfolio with {}\n",
    "            \"\"\".format(\n",
    "                first_name, initial_recommendation\n",
    "            ),\n",
    "        },\n",
    "    )\n",
    "\n",
    "\n",
    "### Intents Dispatcher ###\n",
    "def dispatch(intent_request):\n",
    "    \"\"\"\n",
    "    Called when the user specifies an intent for this bot.\n",
    "    \"\"\"\n",
    "\n",
    "    intent_name = intent_request[\"currentIntent\"][\"name\"]\n",
    "\n",
    "    # Dispatch to bot's intent handlers\n",
    "    if intent_name == \"RecommendPortfolio\":\n",
    "        return recommend_portfolio(intent_request)\n",
    "\n",
    "    raise Exception(\"Intent with name \" + intent_name + \" not supported\")\n",
    "\n",
    "\n",
    "### Main Handler ###\n",
    "def lambda_handler(event, context):\n",
    "    \"\"\"\n",
    "    Route the incoming request based on intent.\n",
    "    The JSON body of the request is provided in the event slot.\n",
    "    \"\"\"\n",
    "\n",
    "    return dispatch(event)"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python [conda env:pyvizenv] *",
   "language": "python",
   "name": "conda-env-pyvizenv-py"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.7.11"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
