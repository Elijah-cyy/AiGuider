package com.example.simpleandroidapp;

import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;

public class MainActivity extends AppCompatActivity {

    private TextView textView;
    private Button button;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // 初始化视图
        textView = findViewById(R.id.textView);
        button = findViewById(R.id.button);

        // 设置按钮点击监听器
        button.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                // 显示Toast消息
                Toast.makeText(MainActivity.this, getString(R.string.button_clicked), Toast.LENGTH_SHORT).show();
                
                // 改变文本视图的文本
                textView.setText(R.string.button_clicked);
            }
        });
    }
} 