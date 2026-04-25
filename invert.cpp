#define NOMINMAX
#include <windows.h>
#include <atomic>
#include <thread>
#include <chrono>
#include <algorithm>
#include <pybind11/pybind11.h>

namespace py = pybind11;

static std::atomic<bool> running(false);
static std::atomic<int> interval_ms(1000);
static std::thread worker;
static HBITMAP screen_backup = nullptr;

int normalize_interval(int timer_ms)
{
    return std::max(1, timer_ms);
}

void capture_screen()
{
    if (screen_backup)
    {
        DeleteObject(screen_backup);
        screen_backup = nullptr;
    }

    HWND hwnd = GetDesktopWindow();
    HDC hdc = GetWindowDC(hwnd);
    HDC memdc = CreateCompatibleDC(hdc);

    RECT r;
    GetWindowRect(hwnd, &r);
    int width = r.right - r.left;
    int height = r.bottom - r.top;

    screen_backup = CreateCompatibleBitmap(hdc, width, height);
    SelectObject(memdc, screen_backup);
    BitBlt(memdc, 0, 0, width, height, hdc, 0, 0, SRCCOPY);

    DeleteDC(memdc);
    ReleaseDC(hwnd, hdc);
}

void restore_screen()
{
    if (!screen_backup)
        return;

    HWND hwnd = GetDesktopWindow();
    HDC hdc = GetWindowDC(hwnd);
    HDC memdc = CreateCompatibleDC(hdc);

    RECT r;
    GetWindowRect(hwnd, &r);
    int width = r.right - r.left;
    int height = r.bottom - r.top;

    SelectObject(memdc, screen_backup);
    BitBlt(hdc, 0, 0, width, height, memdc, 0, 0, SRCCOPY);

    DeleteDC(memdc);
    ReleaseDC(hwnd, hdc);
    DeleteObject(screen_backup);
    screen_backup = nullptr;
}

void invert_loop()
{
    while (running)
    {
        HWND hwnd = GetDesktopWindow();
        HDC hdc = GetWindowDC(hwnd);

        RECT r;
        GetWindowRect(hwnd, &r);
        int width = r.right - r.left;
        int height = r.bottom - r.top;

        BitBlt(hdc, 0, 0, width, height, hdc, 0, 0, NOTSRCCOPY);
        ReleaseDC(hwnd, hdc);

        int remaining_ms = normalize_interval(interval_ms.load());
        while (running && remaining_ms > 0)
        {
            const int sleep_chunk = std::min(remaining_ms, 10);
            std::this_thread::sleep_for(std::chrono::milliseconds(sleep_chunk));
            remaining_ms -= sleep_chunk;
            remaining_ms = std::min(remaining_ms, normalize_interval(interval_ms.load()));
        }
    }
}

int start(int timer_ms = 1000)
{
    interval_ms = normalize_interval(timer_ms);
    if (running)
        return 100;

    capture_screen();
    running = true;
    worker = std::thread(invert_loop);
    return 100;
}

int stop()
{
    if (!running)
        return 100;

    running = false;
    if (worker.joinable())
        worker.join();
    restore_screen();
    return 100;
}

int set_interval(int timer_ms)
{
    interval_ms = normalize_interval(timer_ms);
    return 100;
}

PYBIND11_MODULE(invert, m)
{
    m.def("start", &start, py::arg("timer") = 1000,
          "Start the invert effect with an optional timer interval in milliseconds.");
    m.def("stop", &stop,
          "Stop the invert effect and restore the screen.");
    m.def("setinterval", &set_interval, py::arg("timer"),
          "Set the invert effect interval in milliseconds. Returns 100.");
}
