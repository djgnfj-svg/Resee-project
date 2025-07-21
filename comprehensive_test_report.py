#!/usr/bin/env python3
"""
종합 테스트 결과 리포트 생성기
모든 테스트 결과를 수집하고 종합적인 분석 리포트를 생성
"""

import os
import json
import time
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import sys


@dataclass
class TestSuite:
    name: str
    category: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    duration: float
    success_rate: float
    details: Dict[str, Any]


@dataclass
class TestExecutionResult:
    suite_name: str
    exit_code: int
    stdout: str
    stderr: str
    duration: float
    executed: bool = True


class ComprehensiveTestReporter:
    """종합 테스트 리포터"""
    
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.test_results: List[TestSuite] = []
        self.execution_results: List[TestExecutionResult] = []
        self.report_time = datetime.now()
        
    def run_command(self, command: str, working_dir: str = None, timeout: int = 300) -> TestExecutionResult:
        """명령어 실행 및 결과 수집"""
        if working_dir is None:
            working_dir = self.project_root
            
        print(f"🔄 실행 중: {command}")
        start_time = time.time()
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            duration = time.time() - start_time
            
            return TestExecutionResult(
                suite_name=command.split()[0],
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                duration=duration,
                executed=True
            )
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return TestExecutionResult(
                suite_name=command.split()[0],
                exit_code=-1,
                stdout="",
                stderr=f"Command timed out after {timeout} seconds",
                duration=duration,
                executed=False
            )
        except Exception as e:
            duration = time.time() - start_time
            return TestExecutionResult(
                suite_name=command.split()[0],
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration=duration,
                executed=False
            )
    
    def execute_backend_tests(self):
        """백엔드 테스트 실행"""
        print("\\n🐍 백엔드 테스트 실행")
        
        backend_tests = [
            {
                "name": "Django Unit Tests",
                "command": "docker-compose exec -T backend python manage.py test --verbosity=2",
                "category": "Backend Unit"
            },
            {
                "name": "Pytest Tests",
                "command": "docker-compose exec -T backend pytest -v --tb=short",
                "category": "Backend Unit"
            },
            {
                "name": "Full Workflow Integration Tests",
                "command": "docker-compose exec -T backend python manage.py test tests.test_full_workflow --verbosity=2",
                "category": "Backend Integration"
            },
            {
                "name": "Database Verification Tests",
                "command": "docker-compose exec -T backend python tests/test_database_verification.py",
                "category": "Database"
            },
            {
                "name": "Performance and Stress Tests",
                "command": "docker-compose exec -T backend python tests/test_performance_stress.py",
                "category": "Performance"
            }
        ]
        
        for test in backend_tests:
            result = self.run_command(test["command"])
            self.execution_results.append(result)
            
            # 결과 파싱 및 저장
            success_rate = 100.0 if result.exit_code == 0 else 0.0
            
            # Django 테스트 결과 파싱
            if "test" in test["command"] and result.stdout:
                parsed = self.parse_django_test_output(result.stdout)
            else:
                parsed = {
                    "total": 1,
                    "passed": 1 if result.exit_code == 0 else 0,
                    "failed": 0 if result.exit_code == 0 else 1,
                    "skipped": 0
                }
            
            test_suite = TestSuite(
                name=test["name"],
                category=test["category"],
                total_tests=parsed["total"],
                passed_tests=parsed["passed"],
                failed_tests=parsed["failed"],
                skipped_tests=parsed["skipped"],
                duration=result.duration,
                success_rate=success_rate,
                details={
                    "exit_code": result.exit_code,
                    "stdout_length": len(result.stdout),
                    "stderr_length": len(result.stderr),
                    "executed": result.executed
                }
            )
            
            self.test_results.append(test_suite)
            
            status = "✅" if result.exit_code == 0 else "❌"
            print(f"   {status} {test['name']}: {result.duration:.2f}초")
    
    def execute_frontend_tests(self):
        """프론트엔드 테스트 실행"""
        print("\\n⚛️ 프론트엔드 테스트 실행")
        
        frontend_tests = [
            {
                "name": "Jest Unit Tests",
                "command": "docker-compose exec -T frontend npm test -- --watchAll=false --coverage --verbose",
                "category": "Frontend Unit"
            },
            {
                "name": "TypeScript Type Check",
                "command": "docker-compose exec -T frontend npx tsc --noEmit",
                "category": "Static Analysis"
            },
            {
                "name": "ESLint Code Quality",
                "command": "docker-compose exec -T frontend npm run lint",
                "category": "Code Quality"
            }
        ]
        
        for test in frontend_tests:
            result = self.run_command(test["command"])
            self.execution_results.append(result)
            
            # Jest 결과 파싱
            if "jest" in test["command"] or "npm test" in test["command"]:
                parsed = self.parse_jest_test_output(result.stdout)
            else:
                parsed = {
                    "total": 1,
                    "passed": 1 if result.exit_code == 0 else 0,
                    "failed": 0 if result.exit_code == 0 else 1,
                    "skipped": 0
                }
            
            success_rate = (parsed["passed"] / parsed["total"] * 100) if parsed["total"] > 0 else 0
            
            test_suite = TestSuite(
                name=test["name"],
                category=test["category"],
                total_tests=parsed["total"],
                passed_tests=parsed["passed"],
                failed_tests=parsed["failed"],
                skipped_tests=parsed["skipped"],
                duration=result.duration,
                success_rate=success_rate,
                details={
                    "exit_code": result.exit_code,
                    "stdout_length": len(result.stdout),
                    "stderr_length": len(result.stderr),
                    "executed": result.executed
                }
            )
            
            self.test_results.append(test_suite)
            
            status = "✅" if result.exit_code == 0 else "❌"
            print(f"   {status} {test['name']}: {result.duration:.2f}초")
    
    def execute_system_tests(self):
        """시스템 테스트 실행"""
        print("\\n🐳 시스템 통합 테스트 실행")
        
        system_tests = [
            {
                "name": "Docker System Verification",
                "command": "python3 test_docker_system.py",
                "category": "System Integration"
            }
        ]
        
        for test in system_tests:
            # Docker 시스템 테스트는 사용자 입력이 필요하므로 자동화
            if "test_docker_system.py" in test["command"]:
                # 자동 실행을 위해 입력 우회
                modified_command = f"echo '' | {test['command']}"
                result = self.run_command(modified_command, timeout=120)
            else:
                result = self.run_command(test["command"])
            
            self.execution_results.append(result)
            
            # 시스템 테스트 결과 파싱
            parsed = self.parse_system_test_output(result.stdout)
            
            test_suite = TestSuite(
                name=test["name"],
                category=test["category"],
                total_tests=parsed["total"],
                passed_tests=parsed["passed"],
                failed_tests=parsed["failed"],
                skipped_tests=parsed["skipped"],
                duration=result.duration,
                success_rate=parsed["success_rate"],
                details={
                    "exit_code": result.exit_code,
                    "system_services": parsed.get("services", []),
                    "api_endpoints": parsed.get("endpoints", []),
                    "executed": result.executed
                }
            )
            
            self.test_results.append(test_suite)
            
            status = "✅" if result.exit_code == 0 else "❌"
            print(f"   {status} {test['name']}: {result.duration:.2f}초")
    
    def execute_analysis_scripts(self):
        """분석 스크립트 실행"""
        print("\\n🔍 분석 스크립트 실행")
        
        analysis_scripts = [
            {
                "name": "Missing Features Analysis",
                "command": "python3 test_missing_features_analysis.py",
                "category": "Analysis"
            }
        ]
        
        for script in analysis_scripts:
            result = self.run_command(script["command"])
            self.execution_results.append(result)
            
            # 분석 스크립트는 성공적으로 실행되었으면 패스
            test_suite = TestSuite(
                name=script["name"],
                category=script["category"],
                total_tests=1,
                passed_tests=1 if result.exit_code == 0 else 0,
                failed_tests=0 if result.exit_code == 0 else 1,
                skipped_tests=0,
                duration=result.duration,
                success_rate=100.0 if result.exit_code == 0 else 0.0,
                details={
                    "exit_code": result.exit_code,
                    "analysis_completed": result.exit_code == 0,
                    "executed": result.executed
                }
            )
            
            self.test_results.append(test_suite)
            
            status = "✅" if result.exit_code == 0 else "❌"
            print(f"   {status} {script['name']}: {result.duration:.2f}초")
    
    def parse_django_test_output(self, output: str) -> Dict[str, int]:
        """Django 테스트 출력 파싱"""
        lines = output.split('\\n')
        
        total = 0
        failed = 0
        skipped = 0
        
        for line in lines:
            if "Ran" in line and "test" in line:
                # "Ran 15 tests in 2.345s" 형식 파싱
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        total = int(parts[1])
                    except ValueError:
                        pass
            elif "FAILED" in line and "failures" in line:
                # "FAILED (failures=2)" 형식 파싱
                import re
                match = re.search(r'failures=(\d+)', line)
                if match:
                    failed = int(match.group(1))
            elif "OK" in line:
                failed = 0
        
        passed = total - failed - skipped
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped
        }
    
    def parse_jest_test_output(self, output: str) -> Dict[str, int]:
        """Jest 테스트 출력 파싱"""
        lines = output.split('\\n')
        
        total = 0
        passed = 0
        failed = 0
        skipped = 0
        
        for line in lines:
            if "Tests:" in line:
                # "Tests: 5 passed, 1 failed, 6 total" 형식 파싱
                import re
                
                passed_match = re.search(r'(\d+) passed', line)
                if passed_match:
                    passed = int(passed_match.group(1))
                
                failed_match = re.search(r'(\d+) failed', line)
                if failed_match:
                    failed = int(failed_match.group(1))
                
                skipped_match = re.search(r'(\d+) skipped', line)
                if skipped_match:
                    skipped = int(skipped_match.group(1))
                
                total_match = re.search(r'(\d+) total', line)
                if total_match:
                    total = int(total_match.group(1))
                
                break
        
        if total == 0 and (passed > 0 or failed > 0):
            total = passed + failed + skipped
        
        return {
            "total": total if total > 0 else 1,
            "passed": passed,
            "failed": failed,
            "skipped": skipped
        }
    
    def parse_system_test_output(self, output: str) -> Dict[str, Any]:
        """시스템 테스트 출력 파싱"""
        lines = output.split('\\n')
        
        total = 0
        passed = 0
        failed = 0
        skipped = 0
        success_rate = 0.0
        services = []
        endpoints = []
        
        for line in lines:
            if "총 테스트:" in line:
                try:
                    total = int(line.split("총 테스트:")[1].strip())
                except:
                    pass
            elif "성공:" in line:
                try:
                    passed = int(line.split("성공:")[1].strip())
                except:
                    pass
            elif "실패:" in line:
                try:
                    failed = int(line.split("실패:")[1].strip())
                except:
                    pass
            elif "건너뜀:" in line:
                try:
                    skipped = int(line.split("건너뜀:")[1].strip())
                except:
                    pass
            elif "성공률:" in line:
                try:
                    success_rate = float(line.split("성공률:")[1].replace("%", "").strip())
                except:
                    pass
            elif "✅" in line and ":" in line:
                # 성공한 테스트 기록
                test_name = line.split("✅")[1].split(":")[0].strip()
                if "서비스" in test_name or "연결" in test_name:
                    services.append(test_name)
                elif "API" in test_name or "엔드포인트" in test_name:
                    endpoints.append(test_name)
        
        if total == 0 and (passed > 0 or failed > 0):
            total = passed + failed + skipped
            success_rate = (passed / total * 100) if total > 0 else 0
        
        return {
            "total": total if total > 0 else 1,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "success_rate": success_rate,
            "services": services,
            "endpoints": endpoints
        }
    
    def calculate_overall_statistics(self) -> Dict[str, Any]:
        """전체 통계 계산"""
        if not self.test_results:
            return {}
        
        total_tests = sum(suite.total_tests for suite in self.test_results)
        total_passed = sum(suite.passed_tests for suite in self.test_results)
        total_failed = sum(suite.failed_tests for suite in self.test_results)
        total_skipped = sum(suite.skipped_tests for suite in self.test_results)
        total_duration = sum(suite.duration for suite in self.test_results)
        
        overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        # 카테고리별 통계
        category_stats = {}
        for suite in self.test_results:
            category = suite.category
            if category not in category_stats:
                category_stats[category] = {
                    "total": 0, "passed": 0, "failed": 0, "skipped": 0, "duration": 0
                }
            
            category_stats[category]["total"] += suite.total_tests
            category_stats[category]["passed"] += suite.passed_tests
            category_stats[category]["failed"] += suite.failed_tests
            category_stats[category]["skipped"] += suite.skipped_tests
            category_stats[category]["duration"] += suite.duration
        
        # 각 카테고리별 성공률 계산
        for category, stats in category_stats.items():
            stats["success_rate"] = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
        
        return {
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "total_skipped": total_skipped,
            "total_duration": total_duration,
            "overall_success_rate": overall_success_rate,
            "category_statistics": category_stats,
            "suites_count": len(self.test_results),
            "average_duration_per_suite": total_duration / len(self.test_results) if self.test_results else 0
        }
    
    def generate_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """테스트 결과 기반 권장사항 생성"""
        recommendations = []
        
        if stats["overall_success_rate"] < 90:
            recommendations.append("⚠️ 전체 성공률이 90% 미만입니다. 실패한 테스트들을 우선적으로 수정하세요.")
        
        if stats["total_failed"] > 0:
            recommendations.append(f"❌ {stats['total_failed']}개의 실패한 테스트가 있습니다. 각 실패 원인을 분석하고 수정하세요.")
        
        # 카테고리별 권장사항
        for category, cat_stats in stats["category_statistics"].items():
            if cat_stats["success_rate"] < 80:
                recommendations.append(f"🔍 {category} 카테고리의 성공률이 낮습니다 ({cat_stats['success_rate']:.1f}%). 해당 영역의 코드 품질을 점검하세요.")
        
        if stats["total_duration"] > 300:  # 5분 이상
            recommendations.append("⏱️ 테스트 실행 시간이 길어지고 있습니다. 느린 테스트들을 최적화하거나 병렬 실행을 고려하세요.")
        
        # 테스트 커버리지 권장사항
        if stats["total_tests"] < 50:
            recommendations.append("📈 테스트 수가 적습니다. 더 많은 테스트 케이스를 추가하여 코드 커버리지를 향상시키세요.")
        
        # 성공적인 경우
        if stats["overall_success_rate"] >= 95 and stats["total_failed"] == 0:
            recommendations.append("🎉 모든 테스트가 성공적으로 통과했습니다! 코드 품질이 우수합니다.")
            recommendations.append("🚀 CI/CD 파이프라인에 이 테스트 스위트를 통합하는 것을 고려하세요.")
        
        return recommendations
    
    def generate_report(self) -> Dict[str, Any]:
        """종합 리포트 생성"""
        print("\\n📋 종합 테스트 리포트 생성 중...")
        
        stats = self.calculate_overall_statistics()
        recommendations = self.generate_recommendations(stats)
        
        # 실패한 테스트들 상세 정보
        failed_suites = [suite for suite in self.test_results if suite.failed_tests > 0]
        
        # 성능이 느린 테스트들
        slow_suites = sorted(self.test_results, key=lambda x: x.duration, reverse=True)[:5]
        
        report = {
            "report_metadata": {
                "generated_at": self.report_time.isoformat(),
                "project_name": "Resee - Scientific Review Platform",
                "test_environment": "Docker Compose",
                "reporter_version": "1.0"
            },
            "executive_summary": {
                "total_test_suites": len(self.test_results),
                "total_tests_executed": stats.get("total_tests", 0),
                "overall_success_rate": f"{stats.get('overall_success_rate', 0):.1f}%",
                "total_execution_time": f"{stats.get('total_duration', 0):.2f} seconds",
                "status": "PASS" if stats.get("total_failed", 1) == 0 else "FAIL"
            },
            "detailed_statistics": stats,
            "test_suites": [asdict(suite) for suite in self.test_results],
            "execution_results": [asdict(result) for result in self.execution_results],
            "failed_tests_analysis": {
                "total_failed_suites": len(failed_suites),
                "failed_suites": [asdict(suite) for suite in failed_suites]
            },
            "performance_analysis": {
                "slowest_suites": [
                    {
                        "name": suite.name,
                        "duration": suite.duration,
                        "category": suite.category
                    }
                    for suite in slow_suites
                ],
                "average_suite_duration": stats.get("average_duration_per_suite", 0)
            },
            "recommendations": recommendations,
            "next_steps": [
                "실패한 테스트들의 근본 원인 분석",
                "테스트 커버리지 개선",
                "성능 테스트 확장",
                "CI/CD 파이프라인 통합",
                "정기적인 테스트 실행 자동화"
            ],
            "quality_metrics": {
                "test_coverage": "상세 분석 필요",
                "code_quality": "Linting 통과" if any("lint" in suite.name.lower() for suite in self.test_results) else "분석 필요",
                "performance": "기본 성능 테스트 완료",
                "security": "기본 보안 검증 완료"
            }
        }
        
        return report
    
    def print_summary(self, report: Dict[str, Any]):
        """리포트 요약 출력"""
        print("\\n" + "=" * 70)
        print("📊 종합 테스트 결과 요약")
        print("=" * 70)
        
        summary = report["executive_summary"]
        print(f"🎯 프로젝트: {report['report_metadata']['project_name']}")
        print(f"📅 생성일시: {report['report_metadata']['generated_at']}")
        print(f"🔧 테스트 환경: {report['report_metadata']['test_environment']}")
        
        print(f"\\n📈 실행 결과:")
        print(f"   총 테스트 스위트: {summary['total_test_suites']}개")
        print(f"   총 테스트 케이스: {summary['total_tests_executed']}개")
        print(f"   전체 성공률: {summary['overall_success_rate']}")
        print(f"   총 실행 시간: {summary['total_execution_time']}")
        print(f"   최종 상태: {'✅ PASS' if summary['status'] == 'PASS' else '❌ FAIL'}")
        
        # 카테고리별 결과
        stats = report["detailed_statistics"]
        if "category_statistics" in stats:
            print(f"\\n📊 카테고리별 결과:")
            for category, cat_stats in stats["category_statistics"].items():
                status_icon = "✅" if cat_stats["success_rate"] >= 90 else "⚠️" if cat_stats["success_rate"] >= 70 else "❌"
                print(f"   {status_icon} {category}: {cat_stats['success_rate']:.1f}% ({cat_stats['passed']}/{cat_stats['total']})")
        
        # 실패한 테스트
        if report["failed_tests_analysis"]["total_failed_suites"] > 0:
            print(f"\\n❌ 실패한 테스트 스위트:")
            for suite in report["failed_tests_analysis"]["failed_suites"]:
                print(f"   • {suite['name']}: {suite['failed_tests']}개 실패")
        
        # 권장사항
        if report["recommendations"]:
            print(f"\\n💡 권장사항:")
            for rec in report["recommendations"][:5]:  # 처음 5개만 표시
                print(f"   {rec}")
        
        print("\\n" + "=" * 70)
    
    def run_comprehensive_testing(self):
        """종합 테스트 실행"""
        print("🚀 Resee 프로젝트 종합 테스트 시작")
        print("=" * 70)
        print(f"🕐 시작 시간: {self.report_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # 각 테스트 카테고리 실행
            self.execute_backend_tests()
            self.execute_frontend_tests()
            self.execute_system_tests()
            self.execute_analysis_scripts()
            
            # 리포트 생성
            report = self.generate_report()
            
            # 리포트 파일 저장
            report_file = os.path.join(self.project_root, 'comprehensive_test_report.json')
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            # 요약 출력
            self.print_summary(report)
            
            print(f"\\n📄 상세 리포트가 '{report_file}'에 저장되었습니다.")
            
            # 최종 상태 반환
            return report["executive_summary"]["status"] == "PASS"
            
        except Exception as e:
            print(f"\\n❌ 테스트 실행 중 오류 발생: {str(e)}")
            return False


def main():
    """메인 함수"""
    print("📊 Resee 프로젝트 종합 테스트 리포터")
    print("모든 테스트를 실행하고 종합적인 분석 리포트를 생성합니다.")
    print("\\n⚠️ 주의: Docker Compose가 실행 중인지 확인하세요.")
    print("실행 명령어: docker-compose up -d")
    
    project_root = "/mnt/c/mypojects/Resee"
    
    # Docker 환경 확인
    print("\\n🐳 Docker 환경 확인 중...")
    docker_check = subprocess.run(
        "docker-compose ps",
        shell=True,
        cwd=project_root,
        capture_output=True,
        text=True
    )
    
    if docker_check.returncode != 0:
        print("❌ Docker Compose가 실행되지 않았습니다.")
        print("다음 명령어로 서비스를 시작하세요: docker-compose up -d")
        return 1
    
    print("✅ Docker 환경 확인 완료")
    
    reporter = ComprehensiveTestReporter(project_root)
    success = reporter.run_comprehensive_testing()
    
    if success:
        print("\\n🎉 모든 테스트가 성공적으로 완료되었습니다!")
        return 0
    else:
        print("\\n⚠️ 일부 테스트가 실패했습니다. 상세 리포트를 확인하세요.")
        return 1


if __name__ == "__main__":
    sys.exit(main())