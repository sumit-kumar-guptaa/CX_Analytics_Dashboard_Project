# 5-Minute Stakeholder Walkthrough Script

*Audience: non-technical stakeholders (support ops lead, CX manager). Goal: 2 findings, 1 recommendation, no jargon.*

**[0:00–0:45] Set the scene**
"This dashboard covers 9,870 support tickets from 2025, after cleaning up 300 duplicates and 130
incomplete records out of a 10,300-row export. It pulls from three connected tables — customers,
agents, and tickets — so we can slice by channel, category, region, or agent."

**[0:45–2:00] Finding 1 — channel mix**
"Chat is our biggest channel at 34.3% of all tickets — more than Email and Phone combined with
Social Media. *(point to the channel bar chart)* That matters for staffing: if Chat keeps growing,
real-time-response headcount needs to scale with it, not headcount tuned for Email's slower pace."

**[2:00–3:30] Finding 2 — the 24-hour cliff**
"Here's the one number I'd want everyone to remember: tickets resolved within 24 hours average a
4.03 CSAT. Tickets that take longer than 24 hours drop to 2.90 — a 28% fall. *(point to the
bucket chart / heat-map)* This isn't a small effect size, and it's consistent across every
channel — even Phone, our fastest channel, loses almost a full point once a ticket crosses 24
hours."

**[3:30–4:15] Where it's worst**
"Refund and Technical Issue tickets breach that 24-hour line most often — 29% and 27% of the
time respectively. Those two categories are where a faster-resolution push would move the needle
most."

**[4:15–5:00] Recommendation**
"One concrete ask: prioritize faster-resolution workflows — auto-routing rules or extra staffing
during peak hours — specifically for Refund and Technical Issue tickets, and for Email, our
slowest channel by first-response time. That's the lever most likely to move the CSAT number,
not just ticket-count metrics."

*(Close by inviting the audience into the dashboard themselves — the slicers let anyone filter to
their own team's channel/category/region without needing SQL.)*
