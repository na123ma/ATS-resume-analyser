from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Text = Annotated[str, StringConstraints(strip_whitespace=True, max_length=300)]
LongText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=4000)]
Technology = Literal['Python', 'JavaScript', 'React', 'Django', 'SQL', 'Java']
Language = Literal['Python', 'JavaScript', 'Java', 'C++']
Difficulty = Literal['easy', 'medium', 'hard']


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Register(StrictModel):
    full_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=80)]
    email: Text
    password: Annotated[str, StringConstraints(min_length=10, max_length=128)]
    confirm_password: str
    leaderboard_opt_in: bool = False


class Login(StrictModel):
    email: Text
    password: Annotated[str, StringConstraints(min_length=1, max_length=128)]


class ResumeEntry(StrictModel):
    title: Text = ''
    organization: Text = ''
    location: Text = ''
    start: Text = ''
    end: Text = ''
    details: LongText = ''


class ResumeDraft(StrictModel):
    title: Text = 'My resume'
    template: Literal['classic', 'modern', 'compact'] = 'classic'
    full_name: Text = ''
    email: Text = ''
    phone: Text = ''
    location: Text = ''
    links: Annotated[str, StringConstraints(max_length=800)] = ''
    summary: LongText = ''
    skills: list[Text] = Field(default_factory=list, max_length=60)
    education: list[ResumeEntry] = Field(default_factory=list, max_length=10)
    experience: list[ResumeEntry] = Field(default_factory=list, max_length=20)
    projects: list[ResumeEntry] = Field(default_factory=list, max_length=20)
    certifications: list[Text] = Field(default_factory=list, max_length=20)


class StartExam(StrictModel):
    technology: Technology
    mode: Literal['practice', 'ranked'] = 'practice'
    use_ai: bool = True
    monitoring_consent: bool = False
    fullscreen: bool = False


class Answer(StrictModel):
    question_id: Text
    option: int = Field(ge=0, le=3, strict=True)


class ExamEvent(StrictModel):
    event_id: Annotated[str, StringConstraints(min_length=1, max_length=80)]
    kind: Literal['visibility_lost', 'fullscreen_exit', 'paste_attempt', 'copy_attempt', 'connection_gap']


class MCQ(StrictModel):
    question: Annotated[str, StringConstraints(min_length=10, max_length=1200)]
    options: list[Text] = Field(min_length=4, max_length=4)
    correct: int = Field(ge=0, le=3, strict=True)
    explanation: Annotated[str, StringConstraints(min_length=10, max_length=1500)]

    @model_validator(mode='after')
    def unique_options(self):
        if len(set(o.casefold() for o in self.options)) != 4:
            raise ValueError('Options must be distinct')
        return self


class QuestionSet(StrictModel):
    questions: list[MCQ] = Field(min_length=10, max_length=10)

    @model_validator(mode='after')
    def distinct(self):
        if len({q.question.casefold() for q in self.questions}) != 10:
            raise ValueError('Questions must be distinct')
        return self


class StartInterview(StrictModel):
    technology: Technology
    difficulty: Difficulty = 'easy'
    use_ai: bool = True


class InterviewAnswer(StrictModel):
    answer: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=6000)]
    turn: int = Field(ge=0, le=4)


class InterviewFeedback(StrictModel):
    technical: int = Field(ge=0, le=100)
    clarity: int = Field(ge=0, le=100)
    examples: int = Field(ge=0, le=100)
    feedback: LongText
    ideal_answer: LongText
    next_question: Annotated[str, StringConstraints(min_length=10, max_length=1200)]


class ResumeAdvice(StrictModel):
    summary: LongText
    recommendations: list[LongText] = Field(min_length=1, max_length=8)


class StartCoding(StrictModel):
    language: Language
    difficulty: Difficulty
    use_ai: bool = True


class CodeCase(StrictModel):
    stdin: Annotated[str, StringConstraints(max_length=4000)]
    expected: Annotated[str, StringConstraints(max_length=4000)]


class CodeProblem(StrictModel):
    title: Text
    description: LongText
    constraints: LongText
    starter: Annotated[str, StringConstraints(max_length=8000)]
    reference_solution: Annotated[str, StringConstraints(min_length=10, max_length=12000)]
    tests: list[CodeCase] = Field(min_length=5, max_length=8)


class CodeSet(StrictModel):
    questions: list[CodeProblem] = Field(min_length=3, max_length=3)


class CodeSubmission(StrictModel):
    question_id: Text
    source: Annotated[str, StringConstraints(min_length=1, max_length=20000)]
    mode: Literal['run', 'submit'] = 'submit'
