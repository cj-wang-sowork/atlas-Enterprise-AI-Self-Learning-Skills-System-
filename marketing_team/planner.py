"""Local deterministic routing; roles describe functions, not connected agents."""
import re

# Only these authored generic terms may become public search queries.
DOMAINS = {
    'brand': {'triggers': ('brand', 'positioning', '品牌', '定位'),
              'role': 'brand strategist', 'methods': ('01-brand-positioning',),
              'query': 'brand strategy marketing',
              'terms': ('brand', 'branding', 'positioning', 'marketing'),
              'workflow': 'Map audience needs and competitors; draft differentiated positioning with cited evidence.'},
    'social': {'triggers': ('social', 'instagram', 'linkedin', 'facebook', 'tiktok', '社群', '貼文',
                            'content calendar', 'editorial calendar', 'content planning', 'content-planning'),
               'role': 'social operator', 'methods': ('03-social-operating-system', '04-content-pillar-design'),
               'query': 'social media marketing',
               'terms': ('social', 'content', 'marketing', 'linkedin'),
               'workflow': 'Define channel-specific pillars; draft a bounded calendar and review engagement evidence.'},
    'copy': {'triggers': ('copy', 'copywriting', '文案', '撰寫', 'landing page'),
             'role': 'copy writer', 'methods': ('02-product-positioning',),
             'query': 'copywriting marketing', 'terms': ('copywriting', 'copy', 'content', 'marketing'),
             'workflow': 'Extract supported product benefits; draft variants and QA claims, tone and CTA.'},
    'seo': {'triggers': ('seo', 'search engine', '搜尋引擎', '搜索引擎'),
            'role': 'seo specialist', 'methods': ('04-content-pillar-design',),
            'query': 'seo content optimization', 'terms': ('seo', 'search', 'keyword', 'optimization'),
            'workflow': 'Audit search intent and technical evidence; prioritize keyword clusters and content fixes.'},
    'ads': {'triggers': ('ads', 'advertising', 'paid media', 'ppc', '廣告', '投放'),
            'role': 'ads performance specialist', 'methods': ('05-performance-review',),
            'query': 'advertising campaign optimization', 'terms': ('ads', 'advertising', 'campaign', 'ppc'),
            'workflow': 'Review authorized campaign data; diagnose funnel leakage and propose budget-controlled tests.'},
    'email': {'triggers': ('email', 'newsletter', '電子報', '郵件', 'edm'),
              'role': 'email lifecycle specialist', 'methods': ('04-content-pillar-design',),
              'query': 'email marketing newsletter', 'terms': ('email', 'newsletter', 'marketing', 'lifecycle'),
              'workflow': 'Map consented lifecycle segments; draft a sequence and QA consent, links and measurement.'},
    'analytics': {'triggers': ('analytics', 'ga4', 'dashboard', '成效', '分析', '數據'),
                  'role': 'analytics analyst', 'methods': ('05-performance-review',),
                  'query': 'marketing analytics attribution', 'terms': ('analytics', 'attribution', 'dashboard', 'marketing'),
                  'workflow': 'Validate metric definitions and source quality; compare funnel evidence and prioritize experiments.'},
    'research': {'triggers': ('research', 'competitor', 'market research', '研究', '競品', '調查'),
                 'role': 'research analyst', 'methods': ('02-product-positioning',),
                 'query': 'market research competitive analysis', 'terms': ('research', 'competitive', 'market', 'analysis'),
                 'workflow': 'Collect dated primary sources; compare alternatives and separate facts from hypotheses.'},
    'events': {'triggers': ('event', 'events', 'webinar', 'conference', '展覽', '活動', '研討會'),
               'role': 'events planner', 'methods': ('02-product-positioning',),
               'query': 'event marketing planning', 'terms': ('event', 'events', 'webinar', 'marketing'),
               'workflow': 'Define audience and event objective; draft a runbook, conversion path and evidence checklist.'},
}


def _matches(text, trigger):
    if trigger.isascii():
        return re.search(r'(?<![a-z0-9])' + re.escape(trigger) + r'(?![a-z0-9])', text) is not None
    return trigger in text


def plan_task(task):
    if not isinstance(task, str) or not task.strip() or len(task) > 20000:
        raise ValueError('task must be nonempty text of at most 20000 characters')
    text = task.lower()
    evidence = {domain: [trigger for trigger in spec['triggers'] if _matches(text, trigger)]
                for domain, spec in DOMAINS.items()}
    domains = sorted((domain for domain, hits in evidence.items() if hits),
                     key=lambda domain: (-len(evidence[domain]),
                                         min(text.find(trigger) for trigger in evidence[domain])))
    methods = list(dict.fromkeys(method for domain in domains for method in DOMAINS[domain]['methods']))
    if 'linkedin' in text:
        methods.append('06-linkedin-operator-pack')
    return {'status': 'PLANNED' if domains else 'NEEDS_CLARIFICATION', 'domains': domains,
            'questions': [] if domains else ['Which marketing outcome and channel should this task address?'],
            'roles': [DOMAINS[domain]['role'] for domain in domains[:3]],
            'methods': methods,
            'workflow': [{'domain': domain, 'guidance': DOMAINS[domain]['workflow']} for domain in domains],
            'discovery': {'status': 'NOT_REQUESTED_OFFLINE'}, 'executed': False}
