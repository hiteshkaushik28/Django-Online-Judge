import subprocess
from datetime import datetime
import random
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from .models import Problem, Solution, TestCase

COMPILE = ["g++", "temp.cpp"]
RUN = ["./a.out"]

def index(request):
    return render(request, 'judge/index.html')

def list_problems(request):
    problemset = Problem.objects.all()
    context = {'problemset' : problemset}
    return render(request, 'judge/problems_list.html', context)

def detail(request, question_id):
    if request.method == 'GET':
        problem = get_object_or_404(Problem, pk = question_id)
        context = {'problem' : problem}
        return render(request, 'judge/problem.html', context)
    else:
        return submit(request, question_id)

def submit(request, question_id):
    code = request.POST['code']
    with open('temp.cpp', 'w') as file:
        file.write(code)

    _compile = subprocess.run(COMPILE)
    if (_compile.returncode != 0):
        verdict = Solution.Verdict.COMPILATION_ERROR
    else:
        tests = TestCase.objects.filter(problem__id = question_id)
        verdict = Solution.Verdict.Success
        for test in tests:
            input = test.input
            expected = test.output
            try:
                _run = subprocess.run(RUN, stdout=subprocess.PIPE, input=input, encoding='ascii', timeout=1, check=True)
                actual = _run.stdout
                if (expected != actual):
                    verdict = Solution.Verdict.Wrong_Output
                    break
                else:
                    verdict = Solution.Verdict.Success
            except subprocess.TimeoutExpired:
                verdict = Solution.Verdict.Time_Limit_Exceeded
                break
            except Exception as e:
                verdict = Solution.Verdict.Runtime_Error
                print(e)
                break

    sol = Solution(
        problem = Problem.objects.get(pk = question_id),
        verdict = verdict,
        submittedAt = datetime.now
    )
    sol.save()

    return HttpResponseRedirect(reverse('leaderboard'))

def leaderboard(request):
    recent_submissions = Solution.objects.all().order_by('-submittedAt')[:10]
    return render(request, 'judge/leaderboard.html', {"result": recent_submissions})
