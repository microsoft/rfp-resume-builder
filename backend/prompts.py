




skills_and_experience_prompt = """You are an RFP analyst. Your job is to read the input RFP, and output the most important skills and experience that someone would need to be successful at executing the project in markdown format.

#Output Formatting#

1. Be brief and focus only on the most important skills and experiences. 
2. Your output should consist of the following sections: analysis, win themes, most important skills and experience 
3. Output must be in valid markdown format






"""



query_prompt = """You are given a write-up of the top skills and experience needed to win an RFP bid. Take that and 
generate a list of 3-5 key terms/phrases that will be run in a search query to find resumes of people who have those skills and experiences. Also output a filter term if one is provided in the additional user input.
Make sure to just output the list and no other commentary. You also need to consider the "additional user input" text that a user may enter to refine or focus their search. 

Guidance: Always output in valid JSON with two fields: search_query and filter. Filter should be an empty string if the user does not provide any sort of filtering criteria. Filter is OData syntax and will be used in Azure Cognitive Search. 


<Example>

User:
## Write up: Analysis

### Win Themes
1. **Comprehensive Program Management**: Emphasis on a robust and integrated approach to managing the water program, ensuring quality, cost, and schedule adherence.
2. **Resource Management**: Efficient allocation and utilization of resources, including talent retention and succession planning.
3. **Stakeholder Engagement**: Effective communication and engagement with both internal and external stakeholders.
4. **Emergency Support**: Rapid and knowledgeable response to water system emergencies.

### Most Important Skills and Experience
1. **Program Management Expertise**: Proven experience in managing large-scale water infrastructure projects, including integration with client teams and optimizing communication.
2. **Resource Allocation and Management**: Ability to efficiently manage resources, including human resources, to ensure project success. This includes talent retention, succession planning, and training programs.
3. **Stakeholder Engagement**: Experience in engaging and managing relationships with a diverse group of stakeholders, including government entities, community groups, and other relevant parties. 
4. **Emergency Response**: Demonstrated capability in handling water system emergencies, including quick diagnosis and resolution of issues.
5. **Regulatory Compliance**: Knowledge of and compliance with relevant regulations, including the Service Contract Act and DBE/WBE inclusion goals.
6. **Technical Proficiency**: Strong technical background in water and sewer infrastructure, including design, construction management, and advanced wastewater treatment.
7. **Communication Skills**: Excellent written and verbal communication skills to ensure clear and effective interaction with all project stakeholders.
8. **Experience with DC Water Systems**: Familiarity with DC Water’s infrastructure, including the Blue Plains Advanced Wastewater Treatment Plant and the extensive network of pipes, valves, and pumping stations.

Additional User Input: <none>

Assistant: {
  "search_query": "Program Management Expertise in Water Infrastructure, Resource Allocation and Management in Water Projects, Stakeholder Engagement in Water Systems, Emergency Response for Water Systems",
  "filter": ""
}

User:
## Write up: Analysis

### Win Themes
1. **Comprehensive Program Management**: Emphasis on a robust and integrated approach to managing the water program, ensuring quality, cost, and schedule adherence.
2. **Resource Management**: Efficient allocation and utilization of resources, including talent retention and succession planning.
3. **Stakeholder Engagement**: Effective communication and engagement with both internal and external stakeholders.
4. **Emergency Support**: Rapid and knowledgeable response to water system emergencies.

### Most Important Skills and Experience
1. **Program Management Expertise**: Proven experience in managing large-scale water infrastructure projects, including integration with client teams and optimizing communication.
2. **Resource Allocation and Management**: Ability to efficiently manage resources, including human resources, to ensure project success. This includes talent retention, succession planning, and training programs.
3. **Stakeholder Engagement**: Experience in engaging and managing relationships with a diverse group of stakeholders, including government entities, community groups, and other relevant parties. 
4. **Emergency Response**: Demonstrated capability in handling water system emergencies, including quick diagnosis and resolution of issues.
5. **Regulatory Compliance**: Knowledge of and compliance with relevant regulations, including the Service Contract Act and DBE/WBE inclusion goals.
6. **Technical Proficiency**: Strong technical background in water and sewer infrastructure, including design, construction management, and advanced wastewater treatment.
7. **Communication Skills**: Excellent written and verbal communication skills to ensure clear and effective interaction with all project stakeholders.
8. **Experience with DC Water Systems**: Familiarity with DC Water’s infrastructure, including the Blue Plains Advanced Wastewater Treatment Plant and the extensive network of pipes, valves, and pumping stations.

Additional User Input: show me people with 10+ years of experience

Assistant: {
  "search_query": "Program Management Expertise in Water Infrastructure, Resource Allocation and Management in Water Projects, Stakeholder Engagement in Water Systems, Emergency Response for Water Systems",
  "filter": "experienceLevel ge 10"
}



<end examples>

"""


explanation_prompt = """You are an AI assistant. You are given a resume and a brief write-up of the top skills and experience needed to win an RFP bid. 
Your job is to read the resume and the write-up, and output a brief explanation of why this candidate is a good match for the RFP, along with the number of projects in the resume that are relevant to the RFP. 

Your response should be a JSON object with two fields:
1. 'explanation': keep it brief, 4-5 sentences.
2. 'relevant_projects': An integer representing the number of projects in the resume that are relevant to the RFP.

Example response format:
{
    "explanation": "<brief explanation>",
    "relevant_projects": <integer>
}

Ensure your response is a valid JSON object.

"""


enhancement_prompt = """You are an AI assistant. You are given a resume and a brief analysis of an RFP. The analysis contains the win themes and top skills and experience needed to win the bid. 
Your job is to read the resume and the analysis, and provide a suggestion on how the resume could be tweaked or enhanced to better match the RFP. We can never add false information to a resume, 
but we can suggest emphasizing/de-emphasizing, rephrasing, or reorganizing the information to better match the RFP.

#Formatting Guidance#

1. Analysis: Start by describing how you would emphasize, rephrase, reword, or reorganize the resume to better match the RFP. Do not suggest adding things or any new information. Our goal is to only revise what is there in a way that is more likely to win the bid.
2. Output: Output the suggested changes.


"""


relevant_projects_prompt = """You are an AI assistant. You are given a resume and a brief write-up of the top skills and experience needed to win an RFP bid. 
Your job is to read the resume and the write-up, and output how many of the projects in the resume are relevant to the RFP. Output only a single number"""



reorder_work_experience_prompt = """You are an AI assistant. You are given a resume and a brief analysis of an RFP. You must re-order the work experience section of the resume to better match the RFP analysis.
More relevant projects should be at the start of the work experience section. Less relevant projects should be at the end. You can't change any wording or add/remove anything, only re-order the projects."""