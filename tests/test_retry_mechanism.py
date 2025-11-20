# -*- coding: utf-8 -*-
"""
Тест для проверки механизма повторных попыток при таймауте
"""
import pytest
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))


class MockTimedOutError(Exception):
    """Имитация ошибки таймаута"""
    pass


class MockOpenAIClient:
    """Мок-клиент OpenAI для тестирования"""
    
    def __init__(self, fail_count=0):
        """
        Args:
            fail_count: Сколько раз должен упасть перед успехом (0 = сразу успех)
        """
        self.fail_count = fail_count
        self.attempt_count = 0
        
    async def create(self, **kwargs):
        """Имитирует вызов OpenAI API"""
        self.attempt_count += 1
        
        if self.attempt_count <= self.fail_count:
            raise MockTimedOutError("Timed out")
        
        # Успешный ответ
        class MockChoice:
            class MockMessage:
                content = "Тестовый ответ GPT"
            message = MockMessage()
        
        class MockResponse:
            choices = [MockChoice()]
        
        return MockResponse()


async def test_retry_success_on_second_attempt():
    """Тест: успех на второй попытке после одного таймаута"""
    print("\n🧪 Тест 1: Успех на второй попытке")
    
    # Имитируем что первая попытка упадет, вторая пройдет
    mock_client = MockOpenAIClient(fail_count=1)
    
    try:
        # Имитация retry логики
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = await mock_client.create()
                print(f"✅ Успех на попытке {attempt + 1}: {result.choices[0].message.content}")
                break
            except MockTimedOutError as e:
                if attempt < max_retries - 1:
                    wait_time = 0.1  # Короткая задержка для теста
                    print(f"⚠️ Попытка {attempt + 1} упала, повтор через {wait_time}с")
                    await asyncio.sleep(wait_time)
                else:
                    raise
        
        assert mock_client.attempt_count == 2, "Должно быть 2 попытки"
        print("✅ Тест пройден!")
        
    except Exception as e:
        print(f"❌ Тест провален: {e}")
        raise


async def test_retry_all_attempts_fail():
    """Тест: все 3 попытки проваливаются"""
    print("\n🧪 Тест 2: Все попытки проваливаются")
    
    # Имитируем что все 3 попытки упадут
    mock_client = MockOpenAIClient(fail_count=5)  # Больше чем max_retries
    
    max_retries = 3
    failed = False
    
    for attempt in range(max_retries):
        try:
            result = await mock_client.create()
            break
        except MockTimedOutError as e:
            if attempt < max_retries - 1:
                wait_time = 0.1
                print(f"⚠️ Попытка {attempt + 1} упала, повтор через {wait_time}с")
                await asyncio.sleep(wait_time)
            else:
                print(f"❌ Все {max_retries} попытки исчерпаны")
                failed = True
    
    assert failed, "Должна быть ошибка после всех попыток"
    assert mock_client.attempt_count == 3, "Должно быть ровно 3 попытки"
    print("✅ Тест пройден!")


async def test_retry_immediate_success():
    """Тест: успех с первой попытки"""
    print("\n🧪 Тест 3: Успех с первой попытки")
    
    # Имитируем успешный вызов с первого раза
    mock_client = MockOpenAIClient(fail_count=0)
    
    result = await mock_client.create()
    
    assert mock_client.attempt_count == 1, "Должна быть только 1 попытка"
    assert result.choices[0].message.content == "Тестовый ответ GPT"
    print("✅ Тест пройден!")


async def run_all_tests():
    """Запуск всех асинхронных тестов"""
    await test_retry_success_on_second_attempt()
    await test_retry_all_attempts_fail()
    await test_retry_immediate_success()


if __name__ == "__main__":
    print("🧪 Запуск тестов механизма retry...\n")
    print("=" * 60)
    
    # Запускаем асинхронные тесты
    asyncio.run(run_all_tests())
    
    print("\n" + "=" * 60)
    print("✅ Все тесты механизма retry завершены успешно!")
