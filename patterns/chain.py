# Each security question has its own handler linked in a chain: Q1 -> Q2 -> Q3. 
# If any answer is wrong, that handler returns False which stops the chain right there.
# All three have to pass for the user to be allowed to reset their password.

from abc import ABC, abstractmethod


class SecurityQuestionHandler(ABC):

    def __init__(self):
        self._next_handler: SecurityQuestionHandler | None = None

    def set_next(self, handler: "SecurityQuestionHandler") -> "SecurityQuestionHandler":
        # Returns the handler so you can chain: h1.set_next(h2).set_next(h3)
        self._next_handler = handler
        return handler

    @abstractmethod
    def handle(self, user, answers: list[str]) -> bool:
        pass

    def pass_to_next(self, user, answers: list[str]) -> bool:
        if self._next_handler:
            return self._next_handler.handle(user, answers)
        # Reached the end of the chain with no rejections
        return True


class Question1Handler(SecurityQuestionHandler):

    def handle(self, user, answers: list[str]) -> bool:
        if answers[0].strip().lower() != user.security_a1.strip().lower():
            return False
        return self.pass_to_next(user, answers)


class Question2Handler(SecurityQuestionHandler):

    def handle(self, user, answers: list[str]) -> bool:
        if answers[1].strip().lower() != user.security_a2.strip().lower():
            return False
        return self.pass_to_next(user, answers)


class Question3Handler(SecurityQuestionHandler):

    def handle(self, user, answers: list[str]) -> bool:
        if answers[2].strip().lower() != user.security_a3.strip().lower():
            return False
        return self.pass_to_next(user, answers)


class PasswordRecoveryChain:

    def __init__(self):
        # Build the chain Q1 -> Q2 -> Q3
        self._head = Question1Handler()
        q2 = Question2Handler()
        q3 = Question3Handler()
        self._head.set_next(q2).set_next(q3)

    def verify(self, user, answer1: str, answer2: str, answer3: str) -> bool:
        answers = [answer1, answer2, answer3]
        return self._head.handle(user, answers)
