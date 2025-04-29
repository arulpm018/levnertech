from typing import Dict, Any, Union, List

# Detailed decision tree for ISO 27001 Clause 4
# Each clause defines a sequence of numbered questions (steps) with options leading to next steps or verdicts.

decision_trees: Dict[str, Dict[str, Any]] = {
    "4.1": {
        "title": "Understanding the organization and its context",
        "steps": {
            "1": {
                "question": "Does the organization have a defined process (formal or informal) for identifying external issues (e.g., market conditions, regulatory environment, cultural, social factors) relevant to information security?",
                "options": {
                    "Yes": "2",
                    "No": {"verdict": "Major NC"}
                }
            },
            "2": {
                "question": "Does the organization have a defined process for identifying internal issues (e.g., organizational structure, strategic objectives, internal culture, resource constraints) that affect ISMS outcomes?",
                "options": {
                    "Yes": "3",
                    "No": {"verdict": "Major NC"}
                }
            },
            "3": {
                "question": "Where are these issues documented or recorded? (e.g., strategic plan, context analysis document, risk register)",
                "options": {
                    "Clear Documentation": "4",
                    "Partial / Verbal Only": {"verdict": ["Minor NC", "OFI"]}
                }
            },
            "4": {
                "question": "Is there a schedule or trigger to review and update these external/internal issues?",
                "options": {
                    "Regularly Reviewed": "5",
                    "Irregular or Not Formalized": {"verdict": ["Minor NC", "OFI"]}
                }
            },
            "5": {
                "question": "Do the identified issues clearly align with the organization's purpose and influence on the ISMS objectives?",
                "options": {
                    "Yes": {"verdict": "Complied"},
                    "Partially or Vague": {"verdict": ["OFI", "Minor NC"]}
                }
            }
        }
    },
    "4.2": {
        "title": "Understanding the needs and expectations of interested parties",
        "steps": {
            "1": {
                "question": "Does the organization identify all relevant interested parties (e.g., customers, regulators, suppliers, employees) for the ISMS?",
                "options": {
                    "Yes": "2",
                    "No": {"verdict": "Major NC"}
                }
            },
            "2": {
                "question": "Has the organization documented the requirements (legal, regulatory, contractual) of these interested parties?",
                "options": {
                    "Yes": "3",
                    "No": {"verdict": ["Major NC", "Minor NC"]}
                }
            },
            "3": {
                "question": "Has the organization decided which of these requirements are relevant and to be addressed within the ISMS?",
                "options": {
                    "Yes": "4",
                    "No": {"verdict": "Major NC"}
                }
            },
            "4": {
                "question": "Is there documented evidence of how these decisions were made and what was included/excluded?",
                "options": {
                    "Comprehensive": "5",
                    "Partial": {"verdict": ["Minor NC", "OFI"]}
                }
            },
            "5": {
                "question": "Are relevant stakeholders (e.g., leadership, ISMS team) aware of which requirements must be met?",
                "options": {
                    "Yes": {"verdict": "Complied"},
                    "No": {"verdict": "Minor NC"}
                }
            }
        }
    },
    "4.3": {
        "title": "Determining the scope of the information security management system",
        "steps": {
            "1": {
                "question": "Does the organization have a formal or informal process to define the boundaries and applicability of the ISMS?",
                "options": {
                    "Yes": "2",
                    "No": {"verdict": "Major NC"}
                }
            },
            "2": {
                "question": "Did the organization factor in the external/internal issues (4.1) and interested party requirements (4.2) when defining scope?",
                "options": {
                    "Yes": "3",
                    "No": {"verdict": ["Minor NC", "Major NC"]}
                }
            },
            "3": {
                "question": "Does the scope account for activities performed by external parties (outsourcers, partners, vendors) that could affect information security?",
                "options": {
                    "Yes": "4",
                    "No": {"verdict": ["Minor NC", "Major NC"]}
                }
            },
            "4": {
                "question": "Is the scope documented (e.g., in a formal ISMS scope statement) and accessible to relevant stakeholders?",
                "options": {
                    "Yes": "5",
                    "No": {"verdict": "Minor NC"}
                }
            },
            "5": {
                "question": "Does the documented scope clearly specify all locations, assets, and processes included (and excluded), as well as justifications?",
                "options": {
                    "Yes": {"verdict": "Complied"},
                    "Partial": {"verdict": ["OFI", "Minor NC"]}
                }
            }
        }
    },
    "4.4": {
        "title": "Information security management system",
        "steps": {
            "1": {
                "question": "Has the organization established and implemented an ISMS framework (policies, processes, responsibilities) in line with Clause 4.1–4.3?",
                "options": {
                    "Yes": "2",
                    "No": {"verdict": "Major NC"}
                }
            },
            "2": {
                "question": "Is there a mechanism for maintaining the ISMS and updating it as changes occur (e.g., new risks, new technologies)?",
                "options": {
                    "Yes": "3",
                    "No": {"verdict": "Minor NC"}
                }
            },
            "3": {
                "question": "Does the organization document how various processes interact and support information security objectives?",
                "options": {
                    "Fully": "4",
                    "Partially": {"verdict": ["OFI", "Minor NC"]}
                }
            },
            "4": {
                "question": "Are all ISO 27001 clauses (5–10) planned for or already integrated into the ISMS (not just Clause 4)?",
                "options": {
                    "Yes": "5",
                    "No": {"verdict": "Minor NC"}
                }
            },
            "5": {
                "question": "Is the ISMS documentation (manual, procedures, records) readily available to those who need it?",
                "options": {
                    "Yes": {"verdict": "Complied"},
                    "No": {"verdict": ["OFI", "Minor NC"]}
                }
            }
        }
    }
}


def get_question(clause_id: str, step: str) -> str:
    """Return the question text for a given clause and step."""
    tree = decision_trees.get(clause_id)
    if not tree or step not in tree["steps"]:
        raise KeyError(f"Question not found for clause {clause_id}, step {step}")
    return tree["steps"][step]["question"]


def get_options(clause_id: str, step: str) -> List[str]:
    """Return list of option texts for a given clause and step."""
    opts = decision_trees[clause_id]["steps"][step]["options"]
    return list(opts.keys())


def evaluate_answer(
    clause_id: str,
    step: str,
    answer: str
) -> Union[str, Dict[str, Any]]:
    """
    Evaluate an answer to a given question.
    Returns next step (as string) if continuing,
    or a verdict dict if terminal.
    """
    opts = decision_trees[clause_id]["steps"][step]["options"]
    if answer not in opts:
        raise ValueError(f"Invalid answer '{answer}' for clause {clause_id}, step {step}")
    target = opts[answer]
    if isinstance(target, str):
        return target  # next step number
    # terminal
    return {"verdict": target["verdict"]}
