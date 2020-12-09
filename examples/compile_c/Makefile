CC=gcc
OUTPUT=build

all: $(OUTPUT)/main

$(OUTPUT)/%.o: %.c
	mkdir -p $(dir $@)
	$(CC) -MMD -c $< -o $@

$(OUTPUT)/main: $(OUTPUT)/hello.o $(OUTPUT)/main.o
	$(CC) $^ -o $@

clean:
	rm -rf $(OUTPUT)

.PHONY: clean

-include $(OUTPUT)/*.d
