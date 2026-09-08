#include <QApplication>
#include <QWidget>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QGridLayout>
#include <QLabel>
#include <QPushButton>
#include <QProgressBar>
#include <QTimer>
#include <QDateTime>
#include <QHostInfo>
#include <QMouseEvent>
#include <QPainter>
#include <QFrame>

// Interactive Touch Canvas Widget to verify Touchscreen / Mouse input
class TouchCanvas : public QFrame {
    Q_OBJECT
public:
    explicit TouchCanvas(QWidget *parent = nullptr) : QFrame(parent), lastPos(-1, -1), touchCount(0) {
        setMinimumHeight(140);
        setStyleSheet("background-color: #0E131A; border: 2px dashed #00D2FF; border-radius: 8px;");
    }

    int getTouchCount() const { return touchCount; }
    QPoint getLastPos() const { return lastPos; }

protected:
    void mousePressEvent(QMouseEvent *event) override {
        lastPos = event->pos();
        touchCount++;
        update();
        emit touchReceived(lastPos, touchCount);
    }

    void mouseMoveEvent(QMouseEvent *event) override {
        if (event->buttons() & Qt::LeftButton) {
            lastPos = event->pos();
            update();
            emit touchReceived(lastPos, touchCount);
        }
    }

    void paintEvent(QPaintEvent *event) override {
        QFrame::paintEvent(event);
        QPainter painter(this);
        painter.setRenderHint(QPainter::Antialiasing);

        if (lastPos.x() >= 0 && lastPos.y() >= 0) {
            // Draw a glowing touch point
            painter.setBrush(QColor(0, 210, 255, 180));
            painter.setPen(QPen(QColor(255, 255, 255), 2));
            painter.drawEllipse(lastPos, 18, 18);

            painter.setFont(QFont("sans-serif", 10, QFont::Bold));
            painter.setPen(Qt::white);
            painter.drawText(lastPos.x() + 24, lastPos.y() + 5, 
                             QString("Touch: (%1, %2)").arg(lastPos.x()).arg(lastPos.y()));
        } else {
            painter.setFont(QFont("sans-serif", 11));
            painter.setPen(QColor(139, 155, 180));
            painter.drawText(rect(), Qt::AlignCenter, "Tap or Drag here to test Touchscreen / Mouse Input");
        }
    }

signals:
    void touchReceived(QPoint pos, int count);

private:
    QPoint lastPos;
    int touchCount;
};

int main(int argc, char *argv[]) {
    QApplication app(argc, argv);

    QWidget window;
    window.setWindowTitle("Raspberry Pi 5 - Automotive IVI & Qt 6 Cockpit");
    window.resize(960, 560);
    window.setStyleSheet(
        "QWidget { background-color: #0B0E14; color: #E0E6ED; font-family: -apple-system, sans-serif; }"
        "QLabel#header { font-size: 24px; font-weight: bold; color: #00D2FF; margin-bottom: 2px; }"
        "QLabel#sub { font-size: 13px; color: #8B9BB4; margin-bottom: 15px; }"
        "QFrame.card { background-color: #141A23; border: 1px solid #232D3F; border-radius: 10px; padding: 14px; }"
        "QPushButton { background-color: #0066FE; color: white; border: none; padding: 10px 18px; font-size: 13px; font-weight: bold; border-radius: 6px; }"
        "QPushButton:hover { background-color: #267DFF; }"
        "QPushButton:pressed { background-color: #0052CC; }"
        "QProgressBar { border: 1px solid #232D3F; border-radius: 6px; text-align: center; background: #0E131A; height: 18px; }"
        "QProgressBar::chunk { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00D2FF, stop:1 #0066FE); border-radius: 5px; }"
    );

    QVBoxLayout *mainLayout = new QVBoxLayout(&window);
    mainLayout->setContentsMargins(24, 20, 24, 20);

    // Header
    QLabel *header = new QLabel("Raspberry Pi 5 - Automotive IVI & Qt 6 Platform", &window);
    header->setObjectName("header");
    mainLayout->addWidget(header);

    QLabel *subHeader = new QLabel("Bluetooth 5.0 | Multi-Touch | Auto-WiFi | CAN Bus | TigerVNC :1", &window);
    subHeader->setObjectName("sub");
    mainLayout->addWidget(subHeader);

    // 4 Main Feature Cards
    QGridLayout *grid = new QGridLayout();
    grid->setSpacing(16);

    // Card 1: System & Auto-WiFi
    QFrame *netCard = new QFrame(&window);
    netCard->setProperty("class", "card");
    QVBoxLayout *netLayout = new QVBoxLayout(netCard);
    QLabel *netTitle = new QLabel("<b>Network & Discovery</b>", netCard);
    netTitle->setStyleSheet("color: #00D2FF; font-size: 15px;");
    QLabel *hostLabel = new QLabel(QString("Host: %1.local").arg(QHostInfo::localHostName()), netCard);
    QLabel *ipLabel = new QLabel("Wi-Fi / LAN: Auto-DHCP Active", netCard);
    QLabel *sshLabel = new QLabel("SSH: root@raspberrypi5.local", netCard);
    netLayout->addWidget(netTitle);
    netLayout->addWidget(hostLabel);
    netLayout->addWidget(ipLabel);
    netLayout->addWidget(sshLabel);
    netLayout->addStretch();
    grid->addWidget(netCard, 0, 0);

    // Card 2: Bluetooth & Audio
    QFrame *btCard = new QFrame(&window);
    btCard->setProperty("class", "card");
    QVBoxLayout *btLayout = new QVBoxLayout(btCard);
    QLabel *btTitle = new QLabel("<b>Bluetooth & IVI Audio</b>", btCard);
    btTitle->setStyleSheet("color: #38EF7D; font-size: 15px;");
    QLabel *btStatus = new QLabel("BlueZ 5 Stack: Enabled (HFP/A2DP)", btCard);
    QLabel *audioStatus = new QLabel("PipeWire & ALSA: Ready", btCard);
    QLabel *fwStatus = new QLabel("Firmware: BCM43455 / Synaptics", btCard);
    btLayout->addWidget(btTitle);
    btLayout->addWidget(btStatus);
    btLayout->addWidget(audioStatus);
    btLayout->addWidget(fwStatus);
    btLayout->addStretch();
    grid->addWidget(btCard, 0, 1);

    // Card 3: IVI Cluster & CAN Bus Simulation
    QFrame *iviCard = new QFrame(&window);
    iviCard->setProperty("class", "card");
    QVBoxLayout *iviLayout = new QVBoxLayout(iviCard);
    QLabel *iviTitle = new QLabel("<b>Vehicle Telemetry (CAN Bus)</b>", iviCard);
    iviTitle->setStyleSheet("color: #FFB300; font-size: 15px;");
    QLabel *speedLabel = new QLabel("Simulated Speed: 65 km/h", iviCard);
    QProgressBar *speedBar = new QProgressBar(iviCard);
    speedBar->setRange(0, 200);
    speedBar->setValue(65);
    QLabel *canLabel = new QLabel("SocketCAN: can0 / vcan0 ready", iviCard);
    iviLayout->addWidget(iviTitle);
    iviLayout->addWidget(speedLabel);
    iviLayout->addWidget(speedBar);
    iviLayout->addWidget(canLabel);
    iviLayout->addStretch();
    grid->addWidget(iviCard, 1, 0);

    // Card 4: Touch & Remote Display
    QFrame *dispCard = new QFrame(&window);
    dispCard->setProperty("class", "card");
    QVBoxLayout *dispLayout = new QVBoxLayout(dispCard);
    QLabel *dispTitle = new QLabel("<b>Touchscreen & Display</b>", dispCard);
    dispTitle->setStyleSheet("color: #E056FD; font-size: 15px;");
    QLabel *touchLabel = new QLabel("Touch Driver: libinput / tslib / evdev", dispCard);
    QLabel *vncLabel = new QLabel("TigerVNC Server: Port 5901 (Display :1)", dispCard);
    QLabel *touchStatsLabel = new QLabel("Touch Events: 0 registered", dispCard);
    touchStatsLabel->setStyleSheet("color: #00D2FF; font-weight: bold;");
    dispLayout->addWidget(dispTitle);
    dispLayout->addWidget(touchLabel);
    dispLayout->addWidget(vncLabel);
    dispLayout->addWidget(touchStatsLabel);
    dispLayout->addStretch();
    grid->addWidget(dispCard, 1, 1);

    mainLayout->addLayout(grid);

    // Interactive Touch Canvas area
    QLabel *canvasLabel = new QLabel("<b>Multi-Touch & Pointer Interactive Pad:</b>", &window);
    canvasLabel->setStyleSheet("margin-top: 10px; font-size: 13px; color: #8B9BB4;");
    mainLayout->addWidget(canvasLabel);

    TouchCanvas *touchArea = new TouchCanvas(&window);
    mainLayout->addWidget(touchArea);

    // Connect touch events
    QObject::connect(touchArea, &TouchCanvas::touchReceived, [touchStatsLabel](QPoint pos, int count) {
        touchStatsLabel->setText(QString("Touch Events: %1 (At X:%2, Y:%3)").arg(count).arg(pos.x()).arg(pos.y()));
    });

    // Animate IVI gauges slightly to show live UI
    static int speedVal = 65;
    static int direction = 1;
    QTimer *simTimer = new QTimer(&window);
    QObject::connect(simTimer, &QTimer::timeout, [speedBar, speedLabel]() {
        speedVal += direction * 2;
        if (speedVal >= 110) direction = -1;
        if (speedVal <= 50) direction = 1;
        speedBar->setValue(speedVal);
        speedLabel->setText(QString("Simulated Speed: %1 km/h").arg(speedVal));
    });
    simTimer->start(150);

    window.show();
    return app.exec();
}
#include "main.moc"
