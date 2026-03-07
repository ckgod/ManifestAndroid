# Details: setValue()와 postValue()의 차이

## LiveData의 두 가지 값 갱신 메서드 {#two-update-methods}

`LiveData`에서 데이터를 갱신할 때 사용하는 `setValue()`와 `postValue()`는 동일한 결과를 만들어 내는 듯 보이지만, 호출 가능한 스레드와 동기화 동작에서 분명한 차이가 있어 사용 맥락이 서로 다릅니다.

```kotlin
val liveData = MutableLiveData<String>()
```
{title="MutableLiveData.kt"}

### 1. setValue() {#setvalue}

`setValue()`는 데이터를 **동기적으로** 갱신하며, 반드시 **메인 스레드(UI 스레드)에서만** 호출할 수 있습니다. 호출 즉시 값을 적용하고 같은 프레임 안에서 옵저버를 트리거하므로, 이미 메인 스레드에서 작업 중일 때 가장 적합합니다.

```kotlin
fun updateOnMainThread() {
    liveData.setValue("Updated Value") // 메인 스레드에서만 동작
}
```
{title="Example of setValue.kt"}

UI 이벤트 처리, 수명 주기 콜백, 사용자 입력에 반응하는 코드처럼 메인 스레드 컨텍스트 안에서 자연스럽게 호출되는 경로에 잘 맞습니다. 만약 백그라운드 스레드에서 `setValue()`를 호출하면 즉시 예외가 발생합니다.

### 2. postValue() {#postvalue}

`postValue()`는 데이터를 **비동기적으로** 갱신하는 메서드로, **어느 스레드에서든** 호출할 수 있습니다. 호출 시점에 즉시 값을 바꾸지 않고, 메인 스레드에 갱신 작업을 게시(post)하여 안전하게 실행되도록 합니다. 따라서 호출 스레드를 막지 않고도 스레드 안전성을 확보할 수 있습니다.

```kotlin
val liveData = MutableLiveData<String>()

fun updateInBackground() {
    Thread {
        liveData.postValue("Updated Value") // 어떤 스레드에서든 호출 가능
    }.start()
}
```
{title="Example of postValue.kt"}

네트워크 호출, 데이터베이스 쿼리처럼 백그라운드 스레드에서 결과를 받아 UI에 반영해야 할 때 명시적인 스레드 전환 코드 없이 사용할 수 있어 매우 편리합니다.

### postValue() 내부 구현 {#postvalue-internals}

`postValue()`의 내부 구현을 살펴보면, 백그라운드 executor를 통해 메인 스레드로 값을 전달하는 방식임을 확인할 수 있습니다.

```java
protected void postValue(T value) {
    boolean postTask;
    synchronized (mDataLock) {
        postTask = mPendingData == NOT_SET;
        mPendingData = value;
    }
    if (!postTask) {
        return;
    }
    ArchTaskExecutor.getInstance().postToMainThread(mPostValueRunnable);
}
```
{title="postValue internals.java"}

먼저 `mDataLock`으로 동기화한 뒤 `mPendingData`를 새 값으로 업데이트합니다. 이미 처리 대기 중인 작업이 있다면(`postTask == false`) 추가로 작업을 게시하지 않고 바로 반환하여 중복 실행을 방지합니다. 그렇지 않다면 `ArchTaskExecutor`를 통해 `mPostValueRunnable`을 메인 스레드 큐에 등록하고, 메인 스레드가 이를 실행하면서 `mPendingData`의 값을 옵저버에게 전달합니다.

이 구조 때문에 다음과 같이 메인 스레드에서 두 메서드를 연달아 호출하면 직관과 다른 결과가 나옵니다.

```kotlin
liveData.postValue("a")
liveData.setValue("b")
```
{title="OrderingExample.kt"}

`setValue("b")`는 동기적으로 즉시 값을 `"b"`로 바꿉니다. 그러나 잠시 후 메인 스레드가 큐에 쌓여 있던 `mPostValueRunnable`을 처리하면서 값을 다시 `"a"`로 덮어씁니다. 또한 짧은 시간 안에 `postValue()`를 여러 번 호출하면, 메인 스레드가 작업을 처리할 때 마지막으로 설정된 값 하나만 디스패치된다는 점도 기억할 필요가 있습니다.

### 핵심 차이점 {#key-differences}

| 항목 | setValue() | postValue() |
|------|------------|-------------|
| **스레드** | 메인 스레드에서만 호출 가능 | 어떤 스레드에서든 호출 가능 |
| **동기/비동기** | 동기적으로 즉시 값 갱신 | 메인 스레드에 비동기적으로 게시 |
| **사용 사례** | 메인 스레드에서 시작된 UI 업데이트 | 백그라운드 스레드에서의 갱신 또는 비동기 작업 |
| **옵저버 알림** | 같은 프레임 내에서 즉시 트리거 | 메인 스레드가 작업을 처리한 다음 프레임에서 트리거 |

### 일반적인 사용 패턴 {#common-patterns}

-   **`setValue()`를 사용**: 사용자 인터랙션이나 수명 주기 콜백처럼 갱신이 메인 스레드에서 직접 시작되는 경우.
-   **`postValue()`를 사용**: 데이터베이스 조회, 네트워크 요청 등 장시간 작업의 결과를 백그라운드에서 LiveData에 반영해야 하는 경우.

### 요약 {#summary}

`setValue()`와 `postValue()`는 모두 LiveData의 값을 갱신하지만, 스레딩 모델이 다릅니다. `setValue()`는 메인 스레드 한정의 동기 갱신, `postValue()`는 어떤 스레드에서든 호출 가능한 비동기 갱신입니다. 호출 컨텍스트에 맞는 메서드를 선택해야 스레드 안전성과 정확한 갱신 순서를 보장할 수 있으며, 두 메서드를 섞어 쓸 때는 비동기 게시가 동기 갱신을 덮어쓸 수 있다는 점을 항상 염두에 두어야 합니다.
